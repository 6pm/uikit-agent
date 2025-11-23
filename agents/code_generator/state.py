from langgraph.graph import MessagesState


class CodeGenState(MessagesState):
    """
    State for the code generation agent.
    Inherits 'messages' from MessagesState.
    """

    status: str
