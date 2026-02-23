from functools import lru_cache

from cssselect import HTMLTranslator as OriginalHTMLTranslator
from cssselect.xpath import ExpressionError, XPathExpr as OriginalXPathExpr
from cssselect.parser import Element, FunctionalPseudoElement, PseudoElement

from chuscraper.engine.core._types import Any, Protocol, Self

class XPathExpr(OriginalXPathExpr):
    textnode: bool = False
    attribute: str | None = None

    @classmethod
    def from_xpath(cls, xpath: OriginalXPathExpr, textnode: bool = False, attribute: str | None = None) -> Self:
        x = cls(path=xpath.path, element=xpath.element, condition=xpath.condition)
        x.textnode = textnode
        x.attribute = attribute
        return x

    def __str__(self) -> str:
        path = super().__str__()
        if self.textnode:
            if path == "*": path = "text()"
            elif path.endswith("::*/*"): path = path[:-3] + "text()"
            else: path += "/text()"
        if self.attribute is not None:
            if path.endswith("::*/*"): path = path[:-2]
            path += f"/@{self.attribute}"
        return path

    def join(self: Self, combiner: str, other: OriginalXPathExpr, *args: Any, **kwargs: Any) -> Self:
        if not isinstance(other, XPathExpr): raise ValueError(f"Expressions of type XPathExpr can ony join expressions of the same type")
        super().join(combiner, other, *args, **kwargs)
        self.textnode = other.textnode
        self.attribute = other.attribute
        return self

class TranslatorProtocol(Protocol):
    def xpath_element(self, selector: Element) -> OriginalXPathExpr: pass
    def css_to_xpath(self, css: str, prefix: str = ...) -> str: pass

class TranslatorMixin:
    def xpath_element(self: TranslatorProtocol, selector: Element) -> XPathExpr:
        xpath = super().xpath_element(selector)
        return XPathExpr.from_xpath(xpath)

    def xpath_pseudo_element(self, xpath: OriginalXPathExpr, pseudo_element: PseudoElement) -> OriginalXPathExpr:
        if isinstance(pseudo_element, FunctionalPseudoElement):
            method_name = f"xpath_{pseudo_element.name.replace('-', '_')}_functional_pseudo_element"
            method = getattr(self, method_name, None)
            if not method: raise ExpressionError(f"The functional pseudo-element ::{pseudo_element.name}() is unknown")
            xpath = method(xpath, pseudo_element)
        else:
            method_name = f"xpath_{pseudo_element.replace('-', '_')}_simple_pseudo_element"
            method = getattr(self, method_name, None)
            if not method: raise ExpressionError(f"The pseudo-element ::{pseudo_element} is unknown")
            xpath = method(xpath)
        return xpath

    @staticmethod
    def xpath_attr_functional_pseudo_element(xpath: OriginalXPathExpr, function: FunctionalPseudoElement) -> XPathExpr:
        if function.argument_types() not in (["STRING"], ["IDENT"]): raise ExpressionError(f"Expected a single string or ident for ::attr()")
        return XPathExpr.from_xpath(xpath, attribute=function.arguments[0].value)

    @staticmethod
    def xpath_text_simple_pseudo_element(xpath: OriginalXPathExpr) -> XPathExpr:
        return XPathExpr.from_xpath(xpath, textnode=True)

class HTMLTranslator(TranslatorMixin, OriginalHTMLTranslator):
    def css_to_xpath(self, css: str, prefix: str = "descendant-or-self::") -> str:
        return super().css_to_xpath(css, prefix)

translator = HTMLTranslator()

@lru_cache(maxsize=256)
def css_to_xpath(query: str) -> str:
    return translator.css_to_xpath(query)
