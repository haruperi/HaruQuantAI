//product:SQUANT
// Front-end half of the SQAI plugin — the Java servlet half is ServletSQAI.jar.
angular.module('app.sqaichat', ['sqplugin']).run(function (SQAIChatService) {
    // SQAIChatService publishes window.top.aichatInterface — the whole SQX side of the AI
    // chat contract. It has to exist before the chat iframe mounts and before the license
    // arrives over the WebSocket, so it is instantiated eagerly here instead of lazily by
    // whoever happens to need it first.
});
