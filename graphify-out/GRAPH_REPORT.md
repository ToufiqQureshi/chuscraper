# Graph Report - chuscraper  (2026-08-06)

## Corpus Check
- 180 files · ~140,244 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 3898 nodes · 7251 edges · 243 communities (211 shown, 32 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 78 edges (avg confidence: 0.54)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `6c866ea3`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Element
- Tab
- cdp/storage.py
- event_class
- tab.py
- page.py
- accessibility.py
- T_JSON_DICT
- security.py
- T_JSON_DICT
- input_.py
- KeyEvents
- MobileDevice
- cdp/network.py
- T_JSON_DICT
- Selector
- scripts
- SessionManager
- T_JSON_DICT
- README.md
- continue_intercepted_request
- TabMixin
- .to_json
- ElementStateMixin
- Config
- T_JSON_DICT
- .from_json
- .from_json
- .from_json
- .to_json
- TextHandler
- .from_json
- ProtocolException
- cdp/dom.py
- emulation.py
- BaseRequestExpectation
- .from_json
- runtime.py
- RemoteObjectId
- .to_json
- test_tab.py
- .from_json
- .from_json
- Core Concepts
- fetch.py
- BaseFetchInterception
- T_JSON_DICT
- ElementInteractionMixin
- Selectors
- .from_json
- ActionsMixin
- What You Must Do When Invoked
- deprecated
- ExceptionDetails
- stealth.py
- parser.py
- T_JSON_DICT
- get_security_isolation_status
- .from_json
- .from_json
- Browser
- Installation
- .to_json
- TimeDelta
- get_storage_key_for_frame
- import_from_path
- cdp/browser.py
- debugger.py
- .from_json
- T_JSON_DICT
- Features
- get_box_model
- deprecated
- .from_json
- .create
- WindowID
- .from_json
- .to_json
- HumanBehavior
- XPathExpr
- BrowserContextID
- .to_json
- TargetID
- ElementMixin
- .set_window_state
- StorageSystemMixin
- BaseExtractor
- T_JSON_DICT
- BreakpointId
- get_permissions_policy_state
- .from_json
- set_device_metrics_override
- PressureSource
- inspector.py
- ScriptIdentifier
- navigate
- TargetFilter
- .from_json
- .from_json
- ContraDict
- LocalAuthProxy
- AttributesHandler
- set_script_source
- StreamHandle
- .from_json
- NavigationMixin
- .run
- .from_json
- CookieJar
- DownloadExpectation
- process.py
- html_to_markdown
- Crawler
- Mobile Scraping (ADB)
- ScriptId
- SensorType
- .from_json
- .from_json
- T_JSON_DICT
- ._handle_target_update
- CallFrameId
- get_container_for_node
- RequestId
- RequestStage
- TrustTokenOperationDone
- FrameResourceTree
- get_layout_metrics
- .from_json
- .from_json
- .from_json
- get_usage_and_quota
- .to_json
- test_crawler_comprehensive.py
- set_permission
- get_node_for_location
- get_installability_errors
- target.py
- _start_process
- graphify reference: extra exports and benchmark
- Ponytail
- production_advanced_site_template.py
- Viewport
- ExecutionContextId
- .from_json
- window_chrome.js
- Ponytail Help
- Interactions
- Network & Proxies
- get_wasm_bytecode
- can_emulate
- set_virtual_time_policy
- ErrorReason
- WebSocketRequest
- WebSocketHandshakeResponseReceived
- ResourceChangedPriority
- .from_json
- DialogType
- SelectorsGeneration
- Waiting Strategies
- BrowserCommandId
- CompilationCacheParams
- .from_json
- get_shared_storage_entries
- get_trust_tokens
- FailureDumper
- graphify reference: query, path, explain
- Chuscraper Documentation Website 🕷️
- set_emulated_media
- set_safe_area_insets_override
- set_font_sizes
- get_related_website_sets
- AttachedToTarget
- create_target
- _StorageTools
- ponytail-audit/SKILL.md
- Ponytail Gain
- ponytail-review/SKILL.md
- conftest.py
- test_keyinputs.py
- Advanced CDP
- Async Patterns & Concurrency
- Modular Architecture
- WindowState
- AuthChallenge
- delete_storage_bucket
- InterestGroupAccessType
- InterestGroupAuctionFetchType
- SharedStorageAccessScope
- graphify reference: add a URL and watch a folder
- graphify reference: commit hook and native CLAUDE.md integration
- graphify reference: incremental update and cluster-only
- ponytail-debt/SKILL.md
- test_connection_error_raises_exception_and_logs_stderr
- run_adb_command
- test_ai_extraction.py
- HomepageFeatures/index.js
- ._fetch_sitemap
- .extract
- .extract
- VirtualTimeBudgetExpired
- CacheStorageListUpdated
- IndexedDBContentUpdated
- SharedStorageAccessMethod
- StorageBucketsDurability
- .__init__
- CLAUDE.md
- graphify reference: GitHub clone and cross-repo merge
- graphify reference: transcribe video and audio
- test_multiple_browsers_diff_userdata
- cdp/README.md
- notification_permission.js
- screen_props.js
- .claude/CLAUDE.md
- extraction-spec.md
- next_test.sh
- docusaurus.config.js
- sidebars.js
- chuscraper

## God Nodes (most connected - your core abstractions)
1. `event_class()` - 156 edges
2. `Tab` - 98 edges
3. `Browser` - 78 edges
4. `Selector` - 61 edges
5. `NodeId` - 49 edges
6. `TextHandler` - 48 edges
7. `Element` - 47 edges
8. `ElementStateMixin` - 45 edges
9. `Connection` - 38 edges
10. `Selectors` - 35 edges

## Surprising Connections (you probably didn't know these)
- `test_set_user_agent_defaults_existing_user_agent()` --references--> `Browser`  [EXTRACTED]
  tests/core/test_tab.py → chuscraper/core/browser.py
- `test_set_user_agent_sets_navigator_values()` --references--> `Browser`  [EXTRACTED]
  tests/core/test_tab.py → chuscraper/core/browser.py
- `MockExtractor` --inherits--> `BaseExtractor`  [EXTRACTED]
  tests/test_ai_extraction.py → chuscraper/ai/base.py
- `IO_COUNTERS` --uses--> `Browser`  [INFERRED]
  chuscraper/core/process.py → chuscraper/core/browser.py
- `JOBOBJECT_BASIC_LIMIT_INFORMATION` --uses--> `Browser`  [INFERRED]
  chuscraper/core/process.py → chuscraper/core/browser.py

## Import Cycles
- 3-file cycle: `chuscraper/core/browser.py -> chuscraper/core/util.py -> chuscraper/core/process.py -> chuscraper/core/browser.py`
- 3-file cycle: `chuscraper/__init__.py -> chuscraper/core/element.py -> chuscraper/core/elements/query.py -> chuscraper/__init__.py`
- 3-file cycle: `chuscraper/core/tab.py -> chuscraper/core/tabs/network.py -> chuscraper/core/tabs/base.py -> chuscraper/core/tab.py`
- 3-file cycle: `chuscraper/__init__.py -> chuscraper/core/element.py -> chuscraper/core/elements/interaction.py -> chuscraper/__init__.py`
- 3-file cycle: `chuscraper/__init__.py -> chuscraper/core/element.py -> chuscraper/core/elements/media.py -> chuscraper/__init__.py`
- 3-file cycle: `chuscraper/__init__.py -> chuscraper/core/element.py -> chuscraper/core/elements/state.py -> chuscraper/__init__.py`
- 3-file cycle: `chuscraper/core/element.py -> chuscraper/core/tab.py -> chuscraper/core/tabs/actions.py -> chuscraper/core/element.py`
- 3-file cycle: `chuscraper/core/element.py -> chuscraper/core/tab.py -> chuscraper/core/tabs/dom.py -> chuscraper/core/element.py`
- 3-file cycle: `chuscraper/__init__.py -> chuscraper/core/tab.py -> chuscraper/core/tabs/evaluation.py -> chuscraper/__init__.py`
- 3-file cycle: `chuscraper/core/tab.py -> chuscraper/core/tabs/evaluation.py -> chuscraper/core/tabs/base.py -> chuscraper/core/tab.py`
- 3-file cycle: `chuscraper/__init__.py -> chuscraper/core/tab.py -> chuscraper/core/tabs/navigation.py -> chuscraper/__init__.py`
- 3-file cycle: `chuscraper/core/tab.py -> chuscraper/core/tabs/navigation.py -> chuscraper/core/tabs/base.py -> chuscraper/core/tab.py`
- 3-file cycle: `chuscraper/__init__.py -> chuscraper/core/tab.py -> chuscraper/core/tabs/dom.py -> chuscraper/__init__.py`
- 3-file cycle: `chuscraper/core/tab.py -> chuscraper/core/tabs/dom.py -> chuscraper/core/tabs/base.py -> chuscraper/core/tab.py`
- 3-file cycle: `chuscraper/__init__.py -> chuscraper/core/browser.py -> chuscraper/core/browsers/context.py -> chuscraper/__init__.py`
- 3-file cycle: `chuscraper/core/browser.py -> chuscraper/core/browsers/context.py -> chuscraper/core/browsers/base.py -> chuscraper/core/browser.py`
- 3-file cycle: `chuscraper/__init__.py -> chuscraper/core/browser.py -> chuscraper/core/browsers/target_manager.py -> chuscraper/__init__.py`
- 3-file cycle: `chuscraper/core/browser.py -> chuscraper/core/browsers/target_manager.py -> chuscraper/core/browsers/base.py -> chuscraper/core/browser.py`
- 3-file cycle: `chuscraper/core/browser.py -> chuscraper/core/browsers/target_manager.py -> chuscraper/core/tab.py -> chuscraper/core/browser.py`
- 3-file cycle: `chuscraper/core/tab.py -> chuscraper/core/tabs/screenshot.py -> chuscraper/core/tabs/base.py -> chuscraper/core/tab.py`

## Communities (243 total, 32 thin omitted)

### Community 0 - "Element"
Cohesion: 0.04
Nodes (41): Node, DOM interaction is implemented in terms of mirror objects that represent the…, create(), Element, setter, factory for Elements this is used with Tab.query_selector(_all), since we…, Represents an (HTML) DOM Element :param node: cdp dom node representation…, resolve_node() (+33 more)

### Community 1 - "Tab"
Cohesion: 0.03
Nodes (38): convience function known from selenium., returns the target which was launched with the browser, Shortcut for browser.main_tab.get(url)., Shortcut for browser.main_tab.select(selector)., returns the current targets which are of type "page\, TargetManagerMixin, Any, Path (+30 more)

### Community 2 - "cdp/storage.py"
Cohesion: 0.03
Nodes (65): AttributionReportingReportResult, AttributionReportingReportSent, AttributionReportingVerboseDebugReportSent, CacheStorageContentUpdated, clear_data_for_origin(), clear_data_for_storage_key(), clear_shared_storage_entries(), clear_trust_tokens() (+57 more)

### Community 3 - "event_class"
Cohesion: 0.03
Nodes (50): DataReceived, DirectTCPSocketAborted, DirectTCPSocketChunkReceived, DirectTCPSocketChunkSent, DirectTCPSocketClosed, DirectTCPSocketOpened, DirectUDPSocketAborted, DirectUDPSocketChunkSent (+42 more)

### Community 4 - "tab.py"
Cohesion: 0.08
Nodes (31): AbstractEventLoop, print_banner(), Prints the Chuscraper startup banner once per process., BrowserMixin, Any, Base class for Browser Mixins. Provides shared access to the Browser instance…, BrowserContextMixin, Handles Fetch.authRequired events for proxy authentication. (+23 more)

### Community 5 - "page.py"
Cohesion: 0.03
Nodes (61): add_compilation_cache(), bring_to_front(), capture_snapshot(), clear_compilation_cache(), close(), crash(), disable(), enable() (+53 more)

### Community 6 - "accessibility.py"
Cohesion: 0.06
Nodes (40): AXNode, AXNodeId, AXProperty, AXPropertyName, AXRelatedNode, AXValue, AXValueNativeSourceType, AXValueSource (+32 more)

### Community 7 - "T_JSON_DICT"
Cohesion: 0.06
Nodes (54): collect_class_names_from_subtree(), copy_to(), CSSComputedStyleProperty, DetachedElementInfo, get_anchor_element(), get_attributes(), get_detached_dom_nodes(), get_element_by_relation() (+46 more)

### Community 8 - "security.py"
Cohesion: 0.05
Nodes (37): CertificateError, CertificateErrorAction, CertificateId, CertificateSecurityState, disable(), enable(), handle_certificate_error(), InsecureContentStatus (+29 more)

### Community 9 - "T_JSON_DICT"
Cohesion: 0.06
Nodes (25): AppManifestError, AppManifestParsedProperties, FileFilter, FileHandler, FontFamilies, get_app_manifest(), ImageResource, LaunchHandler (+17 more)

### Community 10 - "input_.py"
Cohesion: 0.07
Nodes (37): cancel_dragging(), dispatch_drag_event(), dispatch_key_event(), dispatch_mouse_event(), dispatch_touch_event(), DragData, DragDataItem, DragIntercepted (+29 more)

### Community 11 - "KeyEvents"
Cohesion: 0.07
Nodes (31): parse_json_event(), Any, T_JSON_DICT, Parse a JSON dictionary into a CDP event., KeyEvents, KeyModifiers, KeyPressEvent, Payload (+23 more)

### Community 12 - "MobileDevice"
Cohesion: 0.06
Nodes (26): get_connected_devices(), Returns a list of connected device serials., Executes an ADB command and returns the output., run_adb(), MobileDevice, Controls a connected Android device via ADB., Swipes from (x1, y1) to (x2, y2)., Types text (must be focused first). Replaces spaces with %s. (+18 more)

### Community 13 - "cdp/network.py"
Cohesion: 0.04
Nodes (37): clear_accepted_encodings_override(), clear_browser_cache(), clear_browser_cookies(), ConnectionType, ContentEncoding, CookieBlockedReason, CookieExemptionReason, disable() (+29 more)

### Community 14 - "T_JSON_DICT"
Cohesion: 0.06
Nodes (21): AssociatedCookie, AuthChallenge, ClientSecurityState, ConnectTiming, DirectUDPMessage, DirectUDPSocketChunkReceived, ExemptedSetCookieWithReason, PostDataEntry (+13 more)

### Community 15 - "Selector"
Cohesion: 0.11
Nodes (4): Any, HtmlElement, Selector, _ElementUnicodeResult

### Community 16 - "scripts"
Cohesion: 0.04
Nodes (44): clsx, @docusaurus/core, @docusaurus/module-type-aliases, @docusaurus/preset-classic, @docusaurus/types, @mdx-js/react, prism-react-renderer, react (+36 more)

### Community 17 - "SessionManager"
Cohesion: 0.06
Nodes (23): AdaptiveRateLimiter, ConcurrencyLimiter, timedelta, RateLimiter, Rate limiting and concurrency control for safe scraping. Implements: - Token…, Get current number of active operations., Manage scraping session duration to avoid suspicion. Automatically tracks…, Initialize session manager. Args: max_duration_minutes: Maximum session… (+15 more)

### Community 18 - "T_JSON_DICT"
Cohesion: 0.08
Nodes (22): get_cookies(), get_shared_storage_metadata(), InterestGroupAuctionEventOccurred, override_quota_for_origin(), T_JSON_DICT, Returns all browser cookies. :param browser_context_id: *(Optional)* Browser…, Override quota for the specified origin **EXPERIMENTAL** :param origin:…, Registers storage key to be notified when an update occurs to its cache storage… (+14 more)

### Community 19 - "README.md"
Cohesion: 0.05
Nodes (39): 🔄 Advanced Selector & Extraction Engine (New!), 🚀 Advanced Switches, ⚡ Async + Fast, ⚙️ Configuration Switches (Parameters), 🛠️ Contributing, 🛠️ Core Switches, 📖 Documentation, 🕵️‍♂️ Dynamic Stealth & Fingerprinting (New!) (+31 more)

### Community 20 - "continue_intercepted_request"
Cohesion: 0.05
Nodes (24): AuthChallengeResponse, continue_intercepted_request(), get_response_body_for_interception(), Headers, InterceptionId, LoaderId, MonotonicTime, float (+16 more)

### Community 21 - "TabMixin"
Cohesion: 0.06
Nodes (19): Any, Base class for Tab components., TabMixin, NetworkMixin, Sets extra HTTP headers for all requests., Enables request interception with given patterns., Simplifies resource blocking. action: 'abort' or 'continue' (default), Returns browser performance metrics. (+11 more)

### Community 22 - ".to_json"
Cohesion: 0.07
Nodes (17): AttributionReportingAggregatableDedupKey, AttributionReportingAggregatableTriggerData, AttributionReportingAggregatableValueDictEntry, AttributionReportingAggregatableValueEntry, AttributionReportingEventTriggerData, AttributionReportingFilterPair, AttributionReportingNamedBudgetCandidate, AttributionReportingSourceRegistrationTimeConfig (+9 more)

### Community 23 - "ElementStateMixin"
Cohesion: 0.06
Nodes (7): BackendNode, Backend node with a friendly name., ElementStateMixin, Any, deprecated, Async version of text_all that uses JS for absolute accuracy in production., Converts this specific element to markdown.

### Community 24 - "Config"
Cohesion: 0.07
Nodes (25): Config, find_binary(), find_executable(), is_root(), Any, BrowserType, PathLike, setter (+17 more)

### Community 25 - "T_JSON_DICT"
Cohesion: 0.07
Nodes (26): clear_geolocation_override(), T_JSON_DICT, Sets a specified page scale factor. **EXPERIMENTAL** :param page_scale_factor:…, Overrides default host system locale with the specified one. **EXPERIMENTAL**…, Allows overriding the automation flag. **EXPERIMENTAL** :param enabled: Whether…, Used to specify User Agent Client Hints to emulate. See…, Clears the overridden Geolocation Position and Error., Requests that page scale factor is reset to initial values. **EXPERIMENTAL** (+18 more)

### Community 26 - ".from_json"
Cohesion: 0.07
Nodes (15): AlternateProtocolUsage, Fired when page is about to send HTTP request., Fired when HTTP response is available., **EXPERIMENTAL** Fired when 103 Early Hints headers is received in addition to…, Source of serviceworker response., The reason why Chrome uses a specific transport protocol for HTTP semantics., ReportingApiEndpointsChangedForOrigin, Request (+7 more)

### Community 27 - ".from_json"
Cohesion: 0.06
Nodes (20): ClientNavigationDisposition, ClientNavigationReason, DownloadWillBegin, FrameClearedScheduledNavigation, FrameDetached, FrameRequestedNavigation, FrameStartedLoading, FrameStoppedLoading (+12 more)

### Community 28 - ".from_json"
Cohesion: 0.06
Nodes (19): CrossOriginIsolatedContextType, DocumentOpened, Frame, FrameNavigated, FrameTree, GatedAPIFeatures, get_frame_tree(), NavigationType (+11 more)

### Community 29 - ".to_json"
Cohesion: 0.07
Nodes (26): CachedResource, CookieParam, get_request_post_data(), get_response_body(), load_network_resource(), LoadNetworkResourceOptions, LoadNetworkResourcePageResult, Information about the cached resource. (+18 more)

### Community 30 - "TextHandler"
Cohesion: 0.09
Nodes (5): Any, Pattern, str, SupportsIndex, TextHandler

### Community 31 - ".from_json"
Cohesion: 0.06
Nodes (17): ChildNodeInserted, CompatibilityMode, DistributedNodesUpdated, get_document(), get_flattened_document(), PseudoElementAdded, PseudoType, deprecated (+9 more)

### Community 32 - "ProtocolException"
Cohesion: 0.07
Nodes (16): ProtocolException, Any, Exception, Transaction, Shortcut to access cdp domains, Saves a screenshot to file., Returns screenshot as bytes., ScreenshotMixin (+8 more)

### Community 33 - "cdp/dom.py"
Cohesion: 0.06
Nodes (26): disable(), discard_search_results(), DocumentUpdated, enable(), hide_highlight(), highlight_node(), highlight_rect(), mark_undoable_state() (+18 more)

### Community 34 - "emulation.py"
Cohesion: 0.06
Nodes (30): clear_device_metrics_override(), clear_device_posture_override(), clear_display_features_override(), clear_idle_override(), Overrides the Idle state. :param is_user_active: Mock isUserActive :param…, Clears Idle state overrides., Switches script execution in the page. :param value: Whether script execution…, Enables touch on platforms which do not support them. :param enabled: Whether… (+22 more)

### Community 35 - "BaseRequestExpectation"
Cohesion: 0.09
Nodes (16): BaseRequestExpectation, Any, Pattern, Base class for handling request and response expectations. This class provides…, Resets the internal state, allowing the expectation to be reused., Get the matched request. :return: The matched request. :rtype:…, Get the matched response. :return: The matched response. :rtype:…, Get the body of the matched response. :return: The response body. :rtype: str (+8 more)

### Community 36 - ".from_json"
Cohesion: 0.07
Nodes (20): AttributeModified, AttributeRemoved, CharacterDataModified, ChildNodeCountUpdated, ChildNodeRemoved, get_search_results(), InlineStyleInvalidated, PseudoElementRemoved (+12 more)

### Community 37 - "runtime.py"
Cohesion: 0.07
Nodes (28): disable(), discard_console_entries(), enable(), ExceptionRevoked, ExecutionContextCreated, get_heap_usage(), get_isolate_id(), Disables reporting of execution contexts creation. (+20 more)

### Community 38 - "RemoteObjectId"
Cohesion: 0.08
Nodes (24): BackendNodeId, describe_node(), focus(), get_file_info(), get_frame_owner(), get_outer_html(), push_nodes_by_backend_ids_to_frontend(), int (+16 more)

### Community 39 - ".to_json"
Cohesion: 0.09
Nodes (21): AdScriptAncestry, AdScriptId, create_isolated_world(), FrameId, get_ad_script_ancestry(), get_origin_trials(), get_resource_content(), OriginTrial (+13 more)

### Community 40 - "test_tab.py"
Cohesion: 0.13
Nodes (27): test_add_handler_module_event(), test_add_handler_type_event(), test_evaluate_complex_object_no_error(), test_evaluate_return_by_value_complex_object(), test_evaluate_return_by_value_falsy(), test_evaluate_return_by_value_simple_json(), test_evaluate_stress_test_complex_objects(), test_expect_download() (+19 more)

### Community 41 - ".from_json"
Cohesion: 0.09
Nodes (17): Cookie, CookiePartitionKey, CookiePriority, CookieSameSite, CookieSourceScheme, delete_cookies(), get_all_cookies(), get_cookies() (+9 more)

### Community 42 - ".from_json"
Cohesion: 0.07
Nodes (18): CompilationCacheProduced, DomContentEventFired, FileChooserOpened, FrameAttached, FrameStartedNavigating, LifecycleEvent, LoadEventFired, print_to_pdf() (+10 more)

### Community 43 - "Core Concepts"
Cohesion: 0.07
Nodes (25): 1. Browser, 2. Tab, 3. Element, 🚀 Advanced Switches, Common Actions, ⚙️ Configuration Switches (Parameters), Core Concepts, 🛠️ Core Switches (+17 more)

### Community 44 - "fetch.py"
Cohesion: 0.13
Nodes (19): AuthChallengeResponse, AuthRequired, continue_request(), continue_with_auth(), disable(), enable(), get_response_body(), T_JSON_DICT (+11 more)

### Community 45 - "BaseFetchInterception"
Cohesion: 0.11
Nodes (13): HeaderEntry, Response HTTP header entry, RequestPattern, BaseFetchInterception, Any, Resets the internal state, allowing the interception to be reused., Get the matched request. :return: The matched request. :rtype:…, Get the body of the matched response. :return: The response body. :rtype: str (+5 more)

### Community 46 - "T_JSON_DICT"
Cohesion: 0.10
Nodes (13): CallFrame, DeepSerializedValue, EntryPreview, ExecutionContextDescription, ExecutionContextsCleared, ObjectPreview, PropertyPreview, T_JSON_DICT (+5 more)

### Community 47 - "ElementInteractionMixin"
Cohesion: 0.16
Nodes (3): ElementInteractionMixin, Any, PathLike

### Community 48 - "Selectors"
Cohesion: 0.10
Nodes (6): TextHandlers, Pattern, slice, SupportsIndex, _T, Selectors

### Community 49 - ".from_json"
Cohesion: 0.08
Nodes (13): DirectSocketDnsQueryType, DirectTCPSocketCreated, DirectTCPSocketOptions, DirectUDPSocketCreated, DirectUDPSocketOptions, Initiator, Information about the request initiator., Fired upon WebSocket creation. (+5 more)

### Community 50 - "ActionsMixin"
Cohesion: 0.12
Nodes (12): ActionsMixin, native click on position x,y :param y: :param x: :param button: str (default =…, Internal helper to implement retry_enabled switch., Finds and clicks an element., Finds and types into an element with optional human-like delay., Finds, clears, and types into an element., Alias for click(mode='human')., Alias for type() with a slightly longer default human delay. (+4 more)

### Community 51 - "What You Must Do When Invoked"
Cohesion: 0.08
Nodes (24): For /graphify add and --watch, For /graphify query, For the commit hook and native CLAUDE.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files (+16 more)

### Community 52 - "deprecated"
Cohesion: 0.08
Nodes (23): clear_device_metrics_override(), clear_device_orientation_override(), clear_geolocation_override(), delete_cookie(), DownloadProgress, FrameScheduledNavigation, get_manifest_icons(), deprecated (+15 more)

### Community 53 - "ExceptionDetails"
Cohesion: 0.13
Nodes (18): await_promise(), compile_script(), evaluate(), ExceptionDetails, get_exception_details(), query_objects(), Compiles expression. :param expression: Expression to compile. :param…, Evaluates expression on global object. :param expression: Expression to… (+10 more)

### Community 54 - "stealth.py"
Cohesion: 0.12
Nodes (11): stealth.py — Advanced Stealth Engine…, Advanced profile for bypassing high-security bot protection., Generates a randomized but standard profile using browserforge., Loads and compiles advanced JS bypass scripts for stealth., SystemProfile, generate_headers(), get_os_name(), js_bypass_path() (+3 more)

### Community 55 - "parser.py"
Cohesion: 0.14
Nodes (13): css_to_xpath(), HTMLTranslator, TypedDict, SetCookieParam, clean_spaces(), flatten(), _is_iterable(), LoggerProxy (+5 more)

### Community 56 - "T_JSON_DICT"
Cohesion: 0.10
Nodes (17): DebugSymbols, disable(), T_JSON_DICT, Activates / deactivates all breakpoints on the page. :param active: New value…, Defines pause on exceptions state. Can be set to stop on all exceptions,…, Debug symbols available for a wasm script., Disables debugger for given page., Resumes JavaScript execution. :param terminate_on_resume: *(Optional)* Set to… (+9 more)

### Community 57 - "get_security_isolation_status"
Cohesion: 0.09
Nodes (9): ContentSecurityPolicySource, ContentSecurityPolicyStatus, CrossOriginEmbedderPolicyStatus, CrossOriginEmbedderPolicyValue, CrossOriginOpenerPolicyStatus, CrossOriginOpenerPolicyValue, get_security_isolation_status(), Returns information about the COEP/COOP isolation status. **EXPERIMENTAL**… (+1 more)

### Community 58 - ".from_json"
Cohesion: 0.09
Nodes (12): Information about a signed exchange signature.…, Information about a signed exchange header.…, Field type for a signed exchange related error., Information about a signed exchange response., Information about a signed exchange response., **EXPERIMENTAL** Fired when a signed exchange was received over the network, SignedExchangeError, SignedExchangeErrorField (+4 more)

### Community 59 - ".from_json"
Cohesion: 0.09
Nodes (8): AttributionReportingEventReportWindows, AttributionReportingNamedBudgetDef, AttributionReportingSourceRegistered, AttributionReportingSourceRegistration, AttributionReportingSourceRegistrationResult, AttributionReportingSourceType, AttributionReportingTriggerDataMatching, AttributionScopesData

### Community 60 - "Browser"
Cohesion: 0.11
Nodes (13): Browser, Returns all open targets/tabs., wait for <time> seconds., Grants all possible permissions to an origin., The Browser object is the "root" of the hierarchy and contains a reference to…, constructor. to create a instance, use :py:meth:`Browser.create(...)`, get_registered_instances(), test_browser_stop_can_be_called_multiple_times() (+5 more)

### Community 61 - "Installation"
Cohesion: 0.09
Nodes (20): Browser not found, First launch (recommended baseline), Install via pip, Installation, Optional launch switches, Requirements, Troubleshooting, Verify installation (+12 more)

### Community 62 - ".to_json"
Cohesion: 0.12
Nodes (16): BreakLocation, continue_to_location(), get_possible_breakpoints(), Location, LocationRange, Changes return value in top frame. Available only at return break position.…, Location range within one script., Steps into the function call. :param break_on_async_call: **(EXPERIMENTAL)**… (+8 more)

### Community 63 - "TimeDelta"
Cohesion: 0.10
Nodes (10): float, str, Primitive value which cannot be JSON-stringified. Includes values ``-0``,…, Number of milliseconds since epoch., Number of milliseconds., Unique identifier of current debugger., TimeDelta, Timestamp (+2 more)

### Community 64 - "get_storage_key_for_frame"
Cohesion: 0.12
Nodes (9): get_storage_key_for_frame(), InterestGroupAuctionId, str, Protected audience interest group auction identifier., Returns a storage key given a frame id. :param frame_id: :returns:, SerializedStorageKey, SignedInt64AsBase10, UnsignedInt128AsBase16 (+1 more)

### Community 65 - "import_from_path"
Cohesion: 0.16
Nodes (16): import_from_path(), ModuleType, Path, MockerFixture, test_account_creation_tutorial_1(), test_account_creation_tutorial_2(), MockerFixture, test_api_responses_tutorial_1() (+8 more)

### Community 66 - "cdp/browser.py"
Cohesion: 0.10
Nodes (17): add_privacy_sandbox_enrollment_override(), close(), crash(), crash_gpu_process(), DownloadProgress, DownloadWillBegin, get_browser_command_line(), PermissionType (+9 more)

### Community 67 - "debugger.py"
Cohesion: 0.12
Nodes (17): disassemble_wasm_module(), next_wasm_disassembly_chunk(), pause(), Makes page not interrupt on any pauses (breakpoint, exception, dom exception…, Steps out of the function call., Fired when the virtual machine resumed execution., **EXPERIMENTAL** :param script_id: Id of the script to disassemble :returns: A…, Disassemble the next chunk of lines for the module corresponding to the stream.… (+9 more)

### Community 68 - ".from_json"
Cohesion: 0.13
Nodes (11): enable(), Paused, Fired when the virtual machine stopped on breakpoint or exception or any other…, Fired when virtual machine fails to parse the script., Fired when virtual machine parses script. This event is also fired for all…, Enum of possible script languages., Enables debugger for the given page. Clients should not assume that the…, ResolvedBreakpoint (+3 more)

### Community 69 - "T_JSON_DICT"
Cohesion: 0.13
Nodes (15): clear(), disable(), enable(), EntryAdded, LogEntry, T_JSON_DICT, Violation configuration setting., Disables log domain, prevents further log entries from being reported to the… (+7 more)

### Community 70 - "Features"
Cohesion: 0.10
Nodes (18): AI Extraction (LLM Integration), Creating Custom Extractors, Example Output, How It Works, Quick Start: OpenAIExtractor, Why Use AI Extraction?, 1. Multi-Format Extraction, 2. Auto-Saving Files (+10 more)

### Community 71 - "get_box_model"
Cohesion: 0.12
Nodes (10): BoxModel, get_box_model(), get_content_quads(), list, Quad, An array of quad vertices, x immediately followed by y for each point, points…, CSS Shape Outside details., Returns boxes for the given node. :param node_id: *(Optional)* Identifier of… (+2 more)

### Community 72 - "deprecated"
Cohesion: 0.11
Nodes (15): can_clear_browser_cache(), can_clear_browser_cookies(), can_emulate_network_conditions(), InterceptionStage, deprecated, Stages of the interception to begin intercepting. Request will intercept before…, Request pattern for interception., Tells whether clearing browser cache is supported. .. deprecated:: 1.3… (+7 more)

### Community 73 - ".from_json"
Cohesion: 0.11
Nodes (9): BackForwardCacheBlockingDetails, BackForwardCacheNotRestoredExplanation, BackForwardCacheNotRestoredExplanationTree, BackForwardCacheNotRestoredReason, BackForwardCacheNotRestoredReasonType, BackForwardCacheNotUsed, List of not restored reasons for back-forward cache., Types of not restored reasons for back-forward cache. (+1 more)

### Community 74 - ".create"
Cohesion: 0.15
Nodes (7): HTTPApi, Any, BrowserType, PathLike, launches the actual browser, Stop the browser instance, entry point for creating an instance

### Community 75 - "WindowID"
Cohesion: 0.14
Nodes (12): Bounds, get_window_bounds(), get_window_for_target(), int, Get position and size of the browser window. **EXPERIMENTAL** :param window_id:…, Get the browser window that contains the devtools target. **EXPERIMENTAL**…, Browser window bounds information, Set position and/or size of the browser window. **EXPERIMENTAL** :param… (+4 more)

### Community 76 - ".from_json"
Cohesion: 0.11
Nodes (7): OriginTrialStatus, OriginTrialToken, OriginTrialTokenStatus, OriginTrialTokenWithStatus, OriginTrialUsageRestriction, Origin Trial(https://www.chromium.org/blink/origin-trials) support. Status for…, Status for an Origin Trial.

### Community 77 - ".to_json"
Cohesion: 0.15
Nodes (10): get_properties(), InternalPropertyDescriptor, PrivatePropertyDescriptor, PropertyDescriptor, Returns properties of a given object. Object group of the result is inherited…, Releases remote object with given id. :param object_id: Identifier of the…, Object property descriptor., Object internal property descriptor. This property isn't normally visible in… (+2 more)

### Community 78 - "HumanBehavior"
Cohesion: 0.14
Nodes (11): HumanBehavior, Human-like behavior simulation for anti-detection. This module provides…, Simulate random mouse movements on the page. Args: page: Browser page object…, Wait on page to simulate reading/browsing time. Args: min_sec: Minimum dwell…, Complete realistic page visit pattern: - Initial page load wait - Scroll…, Simulate human-like browsing behavior to avoid detection., Quick helper for human-like delays., Add a random delay between actions. Args: min_sec: Minimum delay in seconds… (+3 more)

### Community 79 - "XPathExpr"
Cohesion: 0.19
Nodes (9): Any, TranslatorMixin, TranslatorProtocol, XPathExpr, FunctionalPseudoElement, OriginalXPathExpr, Protocol, PseudoElement (+1 more)

### Community 80 - "BrowserContextID"
Cohesion: 0.15
Nodes (13): add_privacy_sandbox_coordinator_key_config(), BrowserContextID, cancel_download(), grant_permissions(), PrivacySandboxAPI, str, Grant specific permissions to the given origin and reject all others.…, Reset all permission management for all origins. :param browser_context_id:… (+5 more)

### Community 81 - ".to_json"
Cohesion: 0.14
Nodes (13): DisabledImageType, Updates the sensor readings reported by a sensor type previously overridden by…, **EXPERIMENTAL** :param image_types: Image types to disable., Allows overriding user agent with the given string. ``userAgentMetadata`` must…, Used to specify User Agent Client Hints to emulate. See…, Enum of image types that can be disabled., Sets or clears an override of the default background color of the frame. This…, SensorReading (+5 more)

### Community 82 - "TargetID"
Cohesion: 0.15
Nodes (11): attach_to_target(), detach_from_target(), deprecated, str, Attaches to the target with given id. :param target_id: :param flatten:…, Unique identifier of attached debugging session., Detaches session with given id. :param session_id: *(Optional)* Session to…, Sends protocol message over session with given id. Consider using flat mode… (+3 more)

### Community 83 - "ElementMixin"
Cohesion: 0.12
Nodes (5): ElementMixin, Base mixin for Element functionality., Position, ElementMediaMixin, PathLike

### Community 84 - ".set_window_state"
Cohesion: 0.12
Nodes (8): get the window Bounds :return: :rtype:, maximize page/tab/window, minimize page/tab/window, minimize page/tab/window, set window size and position :param left: pixels from the left of the screen to…, sets the window size or state., scrolls down maybe :param amount: number in percentage. 25 is a quarter of…, scrolls up maybe :param amount: number in percentage. 25 is a quarter of page,…

### Community 85 - "StorageSystemMixin"
Cohesion: 0.17
Nodes (5): ABC, Any, HtmlElement, SQLiteStorageSystem, StorageSystemMixin

### Community 86 - "BaseExtractor"
Cohesion: 0.21
Nodes (9): BaseExtractor, ABC, Any, Extracts structured data from content using an AI model. :param content: The…, Abstract base class for AI Extractors., OllamaExtractor, Extractor using local Ollama instance (default: http://localhost:11434).…, OpenAIExtractor (+1 more)

### Community 87 - "T_JSON_DICT"
Cohesion: 0.19
Nodes (10): Bucket, get_histogram(), get_histograms(), get_version(), Histogram, T_JSON_DICT, Chrome histogram bucket., Returns version information. :returns: A tuple with the following items: 0.… (+2 more)

### Community 88 - "BreakpointId"
Cohesion: 0.16
Nodes (13): BreakpointId, str, Sets JavaScript breakpoint before each call to the given function. If another…, Breakpoint identifier., Removes JavaScript breakpoint. :param breakpoint_id:, Sets JavaScript breakpoint at a given location. :param location: Location to…, Sets instrumentation breakpoint. :param instrumentation: Instrumentation name.…, Sets JavaScript breakpoint at given location specified either by URL or URL… (+5 more)

### Community 89 - "get_permissions_policy_state"
Cohesion: 0.13
Nodes (8): get_permissions_policy_state(), PermissionsPolicyBlockLocator, PermissionsPolicyBlockReason, PermissionsPolicyFeature, PermissionsPolicyFeatureState, All Permissions Policy features. This enum should match the one defined in…, Get Permissions Policy state on given frame. **EXPERIMENTAL** :param frame_id:…, Reason for a permissions policy feature to be disabled.

### Community 90 - ".from_json"
Cohesion: 0.15
Nodes (7): call_function_on(), CallArgument, CustomPreview, Represents options for serialization. Overrides ``generatePreview`` and…, Represents function call argument. Either remote object id ``objectId``,…, Calls function with given declaration on the given object. Object group of the…, SerializationOptions

### Community 91 - "set_device_metrics_override"
Cohesion: 0.13
Nodes (9): DevicePosture, DisplayFeature, Overrides the values of device screen dimensions (window.screen.width,…, Start reporting the given posture value to the Device Posture API. This…, Start using the given display features to pupulate the Viewport Segments API.…, ScreenOrientation, set_device_metrics_override(), set_device_posture_override() (+1 more)

### Community 92 - "PressureSource"
Cohesion: 0.14
Nodes (9): PressureMetadata, PressureSource, PressureState, Overrides a pressure source of a given type, as used by the Compute Pressure…, TODO: OBSOLETE: To remove when setPressureDataOverride is merged. Provides a…, Provides a given pressure data set that will be processed and eventually be…, set_pressure_data_override(), set_pressure_source_override_enabled() (+1 more)

### Community 93 - "inspector.py"
Cohesion: 0.17
Nodes (11): Detached, disable(), enable(), T_JSON_DICT, Disables inspector domain notifications., Enables inspector domain notifications., Fired when remote debugging connection is about to be terminated. Contains…, Fired when debugging target has crashed (+3 more)

### Community 94 - "ScriptIdentifier"
Cohesion: 0.15
Nodes (11): add_script_to_evaluate_on_load(), add_script_to_evaluate_on_new_document(), str, Deprecated, please use addScriptToEvaluateOnNewDocument instead. ..…, Evaluates given script in every frame upon creation (before loading frame's…, Deprecated, please use removeScriptToEvaluateOnNewDocument instead. ..…, Removes given script from the list. :param identifier:, Unique script identifier. (+3 more)

### Community 95 - "navigate"
Cohesion: 0.14
Nodes (9): get_navigation_history(), navigate(), NavigationEntry, The referring-policy used for the navigation., Returns navigation history for the current page. :returns: A tuple with the…, Navigates current page to the given URL. :param url: URL to navigate the page…, Navigation history entry., ReferrerPolicy (+1 more)

### Community 96 - "TargetFilter"
Cohesion: 0.14
Nodes (11): auto_attach_related(), FilterEntry, list, A filter used by target query/discovery/auto-attach operations., The entries in TargetFilter are matched sequentially against targets and the…, Controls whether to automatically attach to new targets which are considered to…, Adds the specified target to the list of targets that will be monitored for any…, Controls whether to discover available targets and notify via… (+3 more)

### Community 97 - ".from_json"
Cohesion: 0.14
Nodes (7): BlockedReason, CorsError, CorsErrorStatus, LoadingFailed, Fired when HTTP request has failed to load., The reason why request was blocked., The reason why request was blocked.

### Community 98 - ".from_json"
Cohesion: 0.14
Nodes (7): BlockedSetCookieWithReason, IPAddressSpace, Types of reasons why a cookie may not be stored from a response., A cookie which was not stored from a response with the corresponding reason., **EXPERIMENTAL** Fired when additional information about a responseReceived…, ResponseReceivedExtraInfo, SetCookieBlockedReason

### Community 99 - "ContraDict"
Cohesion: 0.27
Nodes (9): cdict(), _check_key(), ContraDict, Any, checks `key` and warns if needed :param key: :param boolean: return True or…, directly inherited from dict accessible by attribute. o.x == o['x'] This works…, _wrap(), attributes are stored here, however, you can set them directly on the element… (+1 more)

### Community 100 - "LocalAuthProxy"
Cohesion: 0.18
Nodes (8): LocalAuthProxy, Local Proxy Forwarder for Chuscraper. Implements the "Patchright Architecture"…, Transfers data between two streams., Starts the local proxy server and returns the port., Stops the server and cleans up all active tasks., Handles a connection from the browser., StreamReader, StreamWriter

### Community 101 - "AttributesHandler"
Cohesion: 0.16
Nodes (3): AttributesHandler, slice, _TextHandlerType

### Community 102 - "set_script_source"
Cohesion: 0.19
Nodes (12): CallFrame, get_stack_trace(), Edits JavaScript source live. In general, functions that are currently on the…, JavaScript call frame. Array of call frames form the call stack., Returns stack trace with given ``stackTraceId``. **EXPERIMENTAL** :param…, Restarts particular call frame from the beginning. The old, deprecated behavior…, restart_frame(), set_script_source() (+4 more)

### Community 103 - "StreamHandle"
Cohesion: 0.21
Nodes (10): close(), str, T_JSON_DICT, This is either obtained from another method or specified as ``blob:<uuid>``…, Close the stream, discard any temporary backing storage. :param handle: Handle…, Read a chunk of the stream :param handle: Handle of the stream to read. :param…, Return UUID of Blob object specified by a remote object id. :param object_id:…, read() (+2 more)

### Community 104 - ".from_json"
Cohesion: 0.15
Nodes (7): The status of a Reporting API report., An object representing a report generated by the Reporting API., **EXPERIMENTAL** Is sent whenever a new report is added. And after…, ReportingApiReport, ReportingApiReportAdded, ReportingApiReportUpdated, ReportStatus

### Community 105 - "NavigationMixin"
Cohesion: 0.17
Nodes (6): NavigationMixin, Any, Reloads the page :param ignore_cache: when set to True (default), it ignores…, Returns the current page title., Sets the geolocation for the tab., Main navigation method.

### Community 106 - ".run"
Cohesion: 0.22
Nodes (7): Any, Checks if the URL belongs to the allowed domains., Removes fragments and normalizes URL., Extracts content based on configured formats OR AI., A worker that picks URLs from the queue and processes them using a Tab., Saves results to a file based on extension., Starts the crawling process.

### Community 107 - ".from_json"
Cohesion: 0.17
Nodes (6): CertificateTransparencyCompliance, Details of a signed certificate timestamp (SCT)., Security details about a request., Whether the request complied with Certificate Transparency policy., SecurityDetails, SignedCertificateTimestamp

### Community 108 - "CookieJar"
Cohesion: 0.21
Nodes (5): CookieJar, PathLike, save all cookies to a file, load all cookies from a file, clear current cookies

### Community 109 - "DownloadExpectation"
Cohesion: 0.21
Nodes (5): DownloadExpectation, Enter the context manager, adding download handler, set download behavior to…, Exit the context manager, removing handler, set download behavior to default., Creates a download expectation for next download. :return: A…, DownloadWillBegin

### Community 110 - "process.py"
Cohesion: 0.21
Nodes (11): _assign_to_job_object(), IO_COUNTERS, JOBOBJECT_BASIC_LIMIT_INFORMATION, JOBOBJECT_EXTENDED_LIMIT_INFORMATION, Any, Path, Popen, Register process cleanup hook for tracked browser PIDs. (+3 more)

### Community 111 - "html_to_markdown"
Cohesion: 0.23
Nodes (7): construct_proxy_dict(), Data extraction utilities for lead scraping. Extractors for: - Markdown…, html_to_markdown(), MarkdownConverter, Robust HTML to Markdown conversion for Chuscraper. Designed to produce "LLM-…, Converts HTML to clean Markdown., Remove excessive newlines and whitespace.

### Community 112 - "Crawler"
Cohesion: 0.24
Nodes (7): Crawler, A Universal Crawler that navigates a website, extracts content, and follows…, main(), main(), main(), stream_handler(), main()

### Community 113 - "Mobile Scraping (ADB)"
Cohesion: 0.17
Nodes (11): Advanced Usage, API Reference, Finding Elements, Handling Dynamic Content, Looping Through Lists, Mobile Scraping (ADB), `MobileDevice`, `MobileElement` (+3 more)

### Community 114 - "ScriptId"
Cohesion: 0.20
Nodes (8): get_script_source(), Search match for resource., Returns source for the script with given id. :param script_id: Id of the script…, Searches for given string in script content. :param script_id: Id of the script…, search_in_content(), SearchMatch, Unique script identifier., ScriptId

### Community 115 - "SensorType"
Cohesion: 0.18
Nodes (7): get_overridden_sensor_information(), Used to specify sensor types to emulate. See…, **EXPERIMENTAL** :param type_: :returns:, Overrides a platform sensor of a given type. If ``enabled`` is true, calls to…, SensorMetadata, SensorType, set_sensor_override_enabled()

### Community 116 - ".from_json"
Cohesion: 0.18
Nodes (5): AdFrameExplanation, AdFrameStatus, AdFrameType, Indicates whether a frame has been identified as an ad., Indicates whether a frame has been identified as an ad and why.

### Community 117 - ".from_json"
Cohesion: 0.20
Nodes (6): attach_to_browser_target(), DetachedFromTarget, Attaches to the browser target, only uses flat sessionId mode. **EXPERIMENTAL**…, **EXPERIMENTAL** Issued when detached from target for any reason (including…, Issued when a target has crashed., TargetCrashed

### Community 118 - "T_JSON_DICT"
Cohesion: 0.25
Nodes (8): create_browser_context(), get_browser_contexts(), T_JSON_DICT, Creates a new empty BrowserContext. Similar to an incognito profile but you can…, Returns all browser contexts created with ``Target.createBrowserContext``…, Enables target discovery for the specified locations, when…, RemoteLocation, set_remote_locations()

### Community 119 - "._handle_target_update"
Cohesion: 0.18
Nodes (8): Issued when a possible inspection target is created., Issued when a target is destroyed., Issued when some information about a target has changed. This only happens…, TargetCreated, TargetDestroyed, TargetInfoChanged, internal handler which updates the targets when chrome emits events, TargetCrashed

### Community 120 - "CallFrameId"
Cohesion: 0.20
Nodes (6): CallFrameId, evaluate_on_call_frame(), Changes value of variable in a callframe. Object-based scopes are not supported…, Call frame identifier., Evaluates expression on a given call frame. :param call_frame_id: Call frame…, set_variable_value()

### Community 121 - "get_container_for_node"
Cohesion: 0.20
Nodes (6): get_container_for_node(), LogicalAxes, PhysicalAxes, ContainerSelector physical axes, Returns the query container of the given node based on container query…, ContainerSelector logical axes

### Community 122 - "RequestId"
Cohesion: 0.20
Nodes (7): continue_response(), fulfill_request(), str, Unique request identifier. Note that this does not identify individual HTTP…, r""" Provides response to the request. :param request_id: An id the client…, r""" Continues loading of the paused response, optionally modifying the…, RequestId

### Community 123 - "RequestStage"
Cohesion: 0.22
Nodes (5): Stages of the request to handle. Request will intercept before the request is…, RequestStage, Resource type as it was perceived by the rendering engine., ResourceType, Sets up interception for network requests matching a URL pattern, request…

### Community 124 - "TrustTokenOperationDone"
Cohesion: 0.20
Nodes (5): **EXPERIMENTAL** Fired exactly once for each Trust Token operation. Depending…, Determines what type of Trust Token operation is executed and depending on the…, TrustTokenOperationDone, TrustTokenOperationType, TrustTokenParams

### Community 125 - "FrameResourceTree"
Cohesion: 0.22
Nodes (6): FrameResource, FrameResourceTree, get_resource_tree(), Returns present frame / resource tree structure. **EXPERIMENTAL** :returns:…, Information about the Resource on the page., Information about the Frame hierarchy along with their cached resources.

### Community 126 - "get_layout_metrics"
Cohesion: 0.24
Nodes (6): get_layout_metrics(), LayoutViewport, Layout viewport position and dimensions., Visual viewport position, dimensions, and scale., Returns metrics relating to the layouting of the page, such as viewport…, VisualViewport

### Community 127 - ".from_json"
Cohesion: 0.20
Nodes (6): BindingCalled, ExecutionContextDestroyed, InspectRequested, **EXPERIMENTAL** Notification is issued every time when binding is called., Issued when execution context is destroyed., Issued when object should be inspected (for example, as a result of inspect()…

### Community 128 - ".from_json"
Cohesion: 0.20
Nodes (4): ConsoleAPICalled, ExceptionThrown, Issued when console API was called., Issued when exception was thrown and unhandled.

### Community 129 - ".from_json"
Cohesion: 0.22
Nodes (3): AttributionReportingAggregatableDebugReportingConfig, AttributionReportingAggregatableDebugReportingData, AttributionReportingAggregationKeysEntry

### Community 130 - "get_usage_and_quota"
Cohesion: 0.22
Nodes (6): get_usage_and_quota(), Returns usage and quota in bytes. :param origin: Security origin. :returns: A…, Enum of possible storage types., Usage for a storage type., StorageType, UsageForType

### Community 131 - ".to_json"
Cohesion: 0.29
Nodes (7): expose_dev_tools_protocol(), get_target_info(), get_targets(), Inject object to the target's main frame that provides a communication channel…, Returns information about a target. **EXPERIMENTAL** :param target_id:…, Retrieves a list of available targets. :param filter_: **(EXPERIMENTAL)**…, TargetInfo

### Community 132 - "test_crawler_comprehensive.py"
Cohesion: 0.29
Nodes (9): cleanup(), main(), Removes temporary test files., Test 1: Single Page Crawl (Depth 0), Test 2: Multi-Format Extraction & Multiple File Types, Test 3: Streaming Callback & Concurrency, test_multi_format_and_files(), test_single_page_crawl() (+1 more)

### Community 133 - "set_permission"
Cohesion: 0.22
Nodes (5): PermissionDescriptor, PermissionSetting, Definition of PermissionDescriptor defined in the Permissions API:…, Set permission settings for given origin. **EXPERIMENTAL** :param permission:…, set_permission()

### Community 134 - "get_node_for_location"
Cohesion: 0.22
Nodes (8): get_node_for_location(), get_node_stack_traces(), Returns node id at given location. Depending on whether DOM domain is enabled,…, Resolves the JavaScript node object for a given NodeId or BackendNodeId. :param…, Gets stack traces associated with a Node. As of now, only provides stack trace…, **EXPERIMENTAL** Called when shadow root is pushed into the element., resolve_node(), ShadowRootPushed

### Community 135 - "get_installability_errors"
Cohesion: 0.25
Nodes (5): get_installability_errors(), InstallabilityError, InstallabilityErrorArgument, The installability error, **EXPERIMENTAL** :returns:

### Community 136 - "target.py"
Cohesion: 0.22
Nodes (8): activate_target(), close_target(), dispose_browser_context(), Activates (focuses) the target. :param target_id:, Closes the target. If the target is a page that gets closed too. :param…, Deletes a BrowserContext. All the belonging pages will be closed without…, Notifies about a new protocol message received from the session (as reported in…, ReceivedMessageFromTarget

### Community 137 - "_start_process"
Cohesion: 0.28
Nodes (8): Path, Popen, Compatibility wrapper around modular process launcher., Compatibility wrapper around modular stderr reader., _read_process_stderr(), _start_process(), test_read_process_stderr_wrapper_returns_text(), test_start_process_wrapper_starts_process()

### Community 138 - "graphify reference: extra exports and benchmark"
Cohesion: 0.22
Nodes (8): graphify reference: extra exports and benchmark, Step 6b - Wiki (only if --wiki flag), Step 7 - Neo4j export (only if --neo4j or --neo4j-push flag), Step 7a - FalkorDB export (only if --falkordb or --falkordb-push flag), Step 7b - SVG export (only if --svg flag), Step 7c - GraphML export (only if --graphml flag), Step 7d - MCP server (only if --mcp flag), Step 8 - Token reduction benchmark (only if total_words > 5000)

### Community 139 - "Ponytail"
Cohesion: 0.22
Nodes (8): Boundaries, Intensity, Output, Persistence, Ponytail, Rules, The ladder, When NOT to be lazy

### Community 140 - "production_advanced_site_template.py"
Cohesion: 0.36
Nodes (8): detect_challenge_or_block(), fetch_advanced_site(), main(), proxy_pool(), Production-ready template for high-friction / bot-protected websites. What this…, Heuristic detector for common challenge/block indicators., Plug your rotating proxies here. Example values: "http://user:pass@resi-…, RunConfig

### Community 141 - "Viewport"
Cohesion: 0.25
Nodes (6): capture_screenshot(), Viewport for capturing screenshot., Capture page screenshot. :param format_: *(Optional)* Image compression format…, Overrides the values of device screen dimensions (window.screen.width,…, set_device_metrics_override(), Viewport

### Community 142 - "ExecutionContextId"
Cohesion: 0.25
Nodes (7): add_binding(), ExecutionContextId, global_lexical_scope_names(), int, Returns all let, const and class variables from global scope. :param…, If executionContextId is empty, adds binding with the given name on the global…, Id of an execution context.

### Community 143 - ".from_json"
Cohesion: 0.25
Nodes (3): AttributionReportingAggregatableResult, AttributionReportingEventLevelResult, AttributionReportingTriggerRegistered

### Community 144 - "window_chrome.js"
Cohesion: 0.25
Nodes (5): makeError, ntEntryFallback, protocolInfo, STATIC_DATA, timingInfo

### Community 145 - "Ponytail Help"
Cohesion: 0.25
Nodes (7): Configure Default Mode, Deactivate, Levels, More, Ponytail Help, Skills, Update

### Community 146 - "Interactions"
Cohesion: 0.25
Nodes (7): Clicking, Interactions, Navigation Properties, Screenshots & Files, Scrolling, Tab Management, Typing & Input

### Community 147 - "Network & Proxies"
Cohesion: 0.25
Nodes (7): Blocking Resources, Modifying Headers, Network & Proxies, Request Interception, Rotating Proxies, Using Proxies, Waiting for Network Idle

### Community 148 - "get_wasm_bytecode"
Cohesion: 0.29
Nodes (7): BreakpointResolved, get_wasm_bytecode(), pause_on_async_call(), deprecated, Fired when breakpoint is resolved to an actual script and location. Deprecated…, This command is deprecated. Use getScriptSource instead. .. deprecated:: 1.3…, .. deprecated:: 1.3 **EXPERIMENTAL** :param parent_stack_trace_id: Debugger…

### Community 149 - "can_emulate"
Cohesion: 0.29
Nodes (7): can_emulate(), deprecated, Overrides value returned by the javascript navigator object. .. deprecated::…, Resizes the frame/viewport of the page. Note that this does not affect the…, Tells whether emulation is supported. .. deprecated:: 1.3 :returns: True if…, set_navigator_overrides(), set_visible_size()

### Community 150 - "set_virtual_time_policy"
Cohesion: 0.29
Nodes (5): Turns on virtual time for all frames (replacing real-time with a synthetic time…, advance: If the scheduler runs out of immediate work, the virtual time base may…, set_virtual_time_policy(), VirtualTimePolicy, TimeSinceEpoch

### Community 151 - "ErrorReason"
Cohesion: 0.29
Nodes (4): fail_request(), Causes the request to fail with specified reason. :param request_id: An id the…, ErrorReason, Network level fetch failure reason.

### Community 152 - "WebSocketRequest"
Cohesion: 0.29
Nodes (4): WebSocket request data., Fired when WebSocket is about to initiate handshake., WebSocketRequest, WebSocketWillSendHandshakeRequest

### Community 153 - "WebSocketHandshakeResponseReceived"
Cohesion: 0.29
Nodes (4): WebSocket response data., Fired when WebSocket handshake response becomes available., WebSocketHandshakeResponseReceived, WebSocketResponse

### Community 154 - "ResourceChangedPriority"
Cohesion: 0.29
Nodes (4): Loading priority of a resource request., **EXPERIMENTAL** Fired when resource loading priority is changed, ResourceChangedPriority, ResourcePriority

### Community 155 - ".from_json"
Cohesion: 0.29
Nodes (3): Source of service worker router., ServiceWorkerRouterInfo, ServiceWorkerRouterSource

### Community 156 - "DialogType"
Cohesion: 0.29
Nodes (4): DialogType, JavascriptDialogOpening, Fired when a JavaScript initiated dialog (alert, confirm, prompt, or…, Javascript dialog type.

### Community 158 - "Waiting Strategies"
Cohesion: 0.29
Nodes (6): Handling Timeouts, Simulating Human Pauses, `wait_for_ready_state`, `wait_for` (The Golden Standard), Waiting for State, Waiting Strategies

### Community 159 - "BrowserCommandId"
Cohesion: 0.33
Nodes (4): BrowserCommandId, execute_browser_command(), Browser command ids used by executeBrowserCommand., Invoke custom browser commands used by telemetry. **EXPERIMENTAL** :param…

### Community 160 - "CompilationCacheParams"
Cohesion: 0.33
Nodes (4): CompilationCacheParams, produce_compilation_cache(), Per-script compilation cache parameters for ``Page.produceCompilationCache``, Requests backend to produce compilation cache for the specified scripts.…

### Community 162 - "get_shared_storage_entries"
Cohesion: 0.40
Nodes (4): get_shared_storage_entries(), Gets the entries in an given origin's shared storage. **EXPERIMENTAL** :param…, Struct for a single key-value pair in an origin's shared storage., SharedStorageEntry

### Community 163 - "get_trust_tokens"
Cohesion: 0.40
Nodes (4): get_trust_tokens(), Returns the number of stored Trust Tokens per issuer for the current browsing…, Pair of issuer origin and number of available (signed, but not used) Trust…, TrustTokens

### Community 164 - "FailureDumper"
Cohesion: 0.33
Nodes (4): FailureDumper, Any, Exception, Production monitor that dumps page state and screenshots on failure.

### Community 165 - "graphify reference: query, path, explain"
Cohesion: 0.33
Nodes (5): For /graphify explain, For /graphify path, graphify reference: query, path, explain, Step 0 — Constrained query expansion (REQUIRED before traversal), Step 1 — Traversal

### Community 166 - "Chuscraper Documentation Website 🕷️"
Cohesion: 0.33
Nodes (5): Building for Production, Chuscraper Documentation Website 🕷️, Local Development, Project Structure, Updating the Docs

### Community 167 - "set_emulated_media"
Cohesion: 0.40
Nodes (3): MediaFeature, Emulates the given media type or media feature for CSS media queries. :param…, set_emulated_media()

### Community 168 - "set_safe_area_insets_override"
Cohesion: 0.40
Nodes (3): Overrides the values for env(safe-area-inset-*) and env(safe-area-max-inset-*).…, SafeAreaInsets, set_safe_area_insets_override()

### Community 169 - "set_font_sizes"
Cohesion: 0.40
Nodes (3): FontSizes, Set default font sizes. **EXPERIMENTAL** :param font_sizes: Specifies font…, set_font_sizes()

### Community 170 - "get_related_website_sets"
Cohesion: 0.50
Nodes (4): get_related_website_sets(), A single Related Website Set object., Returns the effective Related Website Sets in use by this profile for the…, RelatedWebsiteSet

### Community 171 - "AttachedToTarget"
Cohesion: 0.40
Nodes (3): AttachedToTarget, **EXPERIMENTAL** Issued when attached to target because of auto-attach or…, Handles Target.attachedToTarget. Resumes execution if waiting for debugger.

### Community 172 - "create_target"
Cohesion: 0.40
Nodes (4): create_target(), The state of the target window., Creates a new page. :param url: The initial URL the page will be navigated to.…, WindowState

### Community 174 - "ponytail-audit/SKILL.md"
Cohesion: 0.40
Nodes (4): Boundaries, Hunt, Output, Tags

### Community 175 - "Ponytail Gain"
Cohesion: 0.40
Nodes (4): Boundaries, Honesty boundary, Ponytail Gain, Scoreboard

### Community 176 - "ponytail-review/SKILL.md"
Cohesion: 0.40
Nodes (4): Boundaries, Examples, Format, Scoring

### Community 177 - "conftest.py"
Cohesion: 0.60
Nodes (4): fixture, mock_print(), mock_start(), MockerFixture

### Community 178 - "test_keyinputs.py"
Cohesion: 0.40
Nodes (4): Test escape key functionality to close a popup., Test keyboard events with contenteditable div., test_escape_key_popup(), test_visible_events()

### Community 179 - "Advanced CDP"
Cohesion: 0.40
Nodes (4): Advanced CDP, Creating Custom Commands, Listening for Events, Sending Commands

### Community 180 - "Async Patterns & Concurrency"
Cohesion: 0.40
Nodes (4): Async Patterns & Concurrency, Best Practices, Managing Contexts, Parallel Tabs

### Community 181 - "Modular Architecture"
Cohesion: 0.40
Nodes (4): Core module boundaries, Design rules, Modular Architecture, Refactor pattern to follow

### Community 184 - "delete_storage_bucket"
Cohesion: 0.50
Nodes (3): delete_storage_bucket(), Deletes the Storage Bucket with the given storage key and bucket name.…, StorageBucket

### Community 188 - "graphify reference: add a URL and watch a folder"
Cohesion: 0.50
Nodes (3): For /graphify add, For --watch, graphify reference: add a URL and watch a folder

### Community 189 - "graphify reference: commit hook and native CLAUDE.md integration"
Cohesion: 0.50
Nodes (3): For git commit hook, For native CLAUDE.md integration, graphify reference: commit hook and native CLAUDE.md integration

### Community 190 - "graphify reference: incremental update and cluster-only"
Cohesion: 0.50
Nodes (3): For --cluster-only, For --update (incremental re-extraction), graphify reference: incremental update and cluster-only

### Community 191 - "ponytail-debt/SKILL.md"
Cohesion: 0.50
Nodes (3): Boundaries, Output, Scan

### Community 192 - "test_connection_error_raises_exception_and_logs_stderr"
Cohesion: 0.50
Nodes (4): LogCaptureFixture, CreateBrowser, MockerFixture, test_connection_error_raises_exception_and_logs_stderr()

### Community 193 - "run_adb_command"
Cohesion: 0.67
Nodes (3): Runs an ADB command and returns the output., run_adb_command(), test_adb_connection()

## Knowledge Gaps
- **223 isolated node(s):** `isSecure`, `windowScreenProps`, `makeError`, `STATIC_DATA`, `ntEntryFallback` (+218 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **32 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `event_class()` connect `event_class` to `.from_json`, `cdp/storage.py`, `page.py`, `accessibility.py`, `get_node_for_location`, `security.py`, `target.py`, `input_.py`, `KeyEvents`, `cdp/network.py`, `T_JSON_DICT`, `.from_json`, `T_JSON_DICT`, `get_wasm_bytecode`, `WebSocketRequest`, `WebSocketHandshakeResponseReceived`, `.from_json`, `ResourceChangedPriority`, `.from_json`, `.from_json`, `DialogType`, `.from_json`, `cdp/dom.py`, `emulation.py`, `.from_json`, `runtime.py`, `.from_json`, `AttachedToTarget`, `fetch.py`, `T_JSON_DICT`, `.from_json`, `deprecated`, `.from_json`, `.from_json`, `cdp/browser.py`, `debugger.py`, `.from_json`, `T_JSON_DICT`, `VirtualTimeBudgetExpired`, `deprecated`, `.from_json`, `CacheStorageListUpdated`, `IndexedDBContentUpdated`, `inspector.py`, `.from_json`, `.from_json`, `.from_json`, `.from_json`, `._handle_target_update`, `TrustTokenOperationDone`, `.from_json`?**
  _High betweenness centrality (0.100) - this node is a cross-community bridge._
- **Why does `Tab` connect `Tab` to `Element`, `tab.py`, `Selector`, `TabMixin`, `ProtocolException`, `BaseFetchInterception`, `Selectors`, `ActionsMixin`, `stealth.py`, `Browser`, `.__init__`, `ElementMixin`, `.set_window_state`, `NavigationMixin`, `.run`, `DownloadExpectation`, `Crawler`, `._handle_target_update`, `RequestStage`?**
  _High betweenness centrality (0.091) - this node is a cross-community bridge._
- **Why does `Selector` connect `Selector` to `Element`, `Tab`, `tab.py`, `AttributesHandler`, `Selectors`, `parser.py`, `SelectorsGeneration`, `TextHandler`?**
  _High betweenness centrality (0.037) - this node is a cross-community bridge._
- **Are the 14 inferred relationships involving `Tab` (e.g. with `Element` and `SystemProfile`) actually correct?**
  _`Tab` has 14 INFERRED edges - model-reasoned connections that need verification._
- **What connects `isSecure`, `windowScreenProps`, `makeError` to the rest of the system?**
  _223 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Element` be split into smaller, more focused modules?**
  _Cohesion score 0.03892405063291139 - nodes in this community are weakly interconnected._
- **Should `Tab` be split into smaller, more focused modules?**
  _Cohesion score 0.03496503496503497 - nodes in this community are weakly interconnected._