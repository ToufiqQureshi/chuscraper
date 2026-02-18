from __future__ import annotations
from .base import TabMixin
from typing import TYPE_CHECKING, Any, Tuple, Optional, cast
import typing
from ... import cdp
from ..connection import ProtocolException
from ...cdp.runtime import DeepSerializedValue

if TYPE_CHECKING:
    from ..tab import Tab

class EvaluationMixin(TabMixin):
    async def evaluate(
        self, expression: str, await_promise: bool = False, return_by_value: bool = True
    ) -> (
        Any
        | None
        | typing.Tuple[cdp.runtime.RemoteObject, cdp.runtime.ExceptionDetails | None]
    ):
        ser: cdp.runtime.SerializationOptions | None = None
        if not return_by_value:
            ser = cdp.runtime.SerializationOptions(
                serialization="deep",
                max_depth=10,
                additional_parameters={"maxNodeDepth": 10, "includeShadowTree": "all"},
            )

        remote_object, errors = await self.send(
            cdp.runtime.evaluate(
                expression=expression,
                user_gesture=True,
                await_promise=await_promise,
                return_by_value=return_by_value,
                allow_unsafe_eval_blocked_by_csp=True,
                serialization_options=ser,
            )
        )
        if errors:
            raise ProtocolException(errors)

        if return_by_value:
            return remote_object.value
        # deep_serialized_value is guaranteed to be present when
        # serialization_options.serialization="deep"
        return cast(DeepSerializedValue, remote_object.deep_serialized_value).value

    async def js_dumps(
        self, obj_name: str, return_by_value: Optional[bool] = True
    ) -> (
        Any
        | typing.Tuple[cdp.runtime.RemoteObject, cdp.runtime.ExceptionDetails | None]
    ):
        """
        dump given js object with its properties and values as a dict
        """
        js_code_a = (
            """
                           function ___dump(obj, _d = 0) {
                               let _typesA = ['object', 'function'];
                               let _typesB = ['number', 'string', 'boolean'];
                               if (_d == 2) {
                                   console.log('maxdepth reached for ', obj);
                                   return
                               }
                               let tmp = {}
                               for (let k in obj) {
                                   if (obj[k] == window) continue;
                                   let v;
                                   try {
                                       if (obj[k] === null || obj[k] === undefined || obj[k] === NaN) {
                                           console.log('obj[k] is null or undefined or Nan', k, '=>', obj[k])
                                           tmp[k] = obj[k];
                                           continue
                                       }
                                   } catch (e) {
                                       tmp[k] = null;
                                       continue
                                   }


                                   if (_typesB.includes(typeof obj[k])) {
                                       tmp[k] = obj[k]
                                       continue
                                   }

                                   try {
                                       if (typeof obj[k] === 'function') {
                                           tmp[k] = obj[k].toString()
                                           continue
                                       }


                                       if (typeof obj[k] === 'object') {
                                           tmp[k] = ___dump(obj[k], _d + 1);
                                           continue
                                       }


                                   } catch (e) {}

                                   try {
                                       tmp[k] = JSON.stringify(obj[k])
                                       continue
                                   } catch (e) {

                                   }
                                   try {
                                       tmp[k] = obj[k].toString();
                                       continue
                                   } catch (e) {}
                               }
                               return tmp
                           }

                           function ___dumpY(obj) {
                               var objKeys = (obj) => {
                                   var [target, result] = [obj, []];
                                   while (target !== null) {
                                       result = result.concat(Object.getOwnPropertyNames(target));
                                       target = Object.getPrototypeOf(target);
                                   }
                                   return result;
                               }
                               return Object.fromEntries(
                                   objKeys(obj).map(_ => [_, ___dump(obj[_])]))

                           }
                           ___dumpY( %s )
                   """
            % obj_name
        )
        js_code_b = (
            """
            ((obj, visited = new WeakSet()) => {
                 if (visited.has(obj)) {
                     return {}
                 }
                 visited.add(obj)
                 var result = {}, _tmp;
                 for (var i in obj) {
                         try {
                             if (i === 'enabledPlugin' || typeof obj[i] === 'function') {
                                 continue;
                             } else if (typeof obj[i] === 'object') {
                                 _tmp = recurse(obj[i], visited);
                                 if (Object.keys(_tmp).length) {
                                     result[i] = _tmp;
                                 }
                             } else {
                                 result[i] = obj[i];
                             }
                         } catch (error) {
                             # console.error('Error:', error);
                         }
                     }
                return result;
            })(%s)
        """
            % obj_name
        )

        # we're purposely not calling self.evaluate here to prevent infinite loop on certain expressions
        remote_object, exception_details = await self.send(
            cdp.runtime.evaluate(
                js_code_a,
                await_promise=True,
                return_by_value=return_by_value,
                allow_unsafe_eval_blocked_by_csp=True,
            )
        )
        if exception_details:
            # try second variant

            remote_object, exception_details = await self.send(
                cdp.runtime.evaluate(
                    js_code_b,
                    await_promise=True,
                    return_by_value=return_by_value,
                    allow_unsafe_eval_blocked_by_csp=True,
                )
            )

        if exception_details:
            raise ProtocolException(exception_details)
        if return_by_value:
            return remote_object.value
        else:
            return remote_object, exception_details
