# Identification import: missing timer dependency

2026-10-19: user captures image(20261019-175956).png and image(20261019-180031).png show six IDE errors in E_CYCLE: E_DELAY cannot be loaded, followed by unresolved DT, START, STOP and EO endpoints. The standalone identification project omitted E_DELAY. Include the unchanged standard type already used by PID_Whiteboard, preserving its license. No controller algorithm or event wiring changes are required.

Update the feature branch and refresh Adaptive_Identification. Confirm the six errors disappear before export. Native export/build/execution is still pending; disappearance of IDE errors is not yet confirmed by the user.

The second capture shows ENABLE_PROCESS_CHANGE=TRUE and FORGETTING_FACTOR=0.8. For the first fixed-process run set FALSE and 1.0, keeping INITIAL_COVARIANCE=10000.0 and SamplingClock.DT=T#100ms. Save the application.
