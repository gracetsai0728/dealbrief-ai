from agents import ModelBehaviorError


def require_tool_calls(result, required_tool_names):
    called_tool_names = {
        getattr(item, "tool_name", None)
        for item in getattr(result, "new_items", [])
    }
    missing_tool_names = set(required_tool_names) - called_tool_names
    if missing_tool_names:
        missing = ", ".join(sorted(missing_tool_names))
        raise ModelBehaviorError(
            f"The agent did not call the required database tools: {missing}."
        )
