import pytest
import importlib

from Backend.Routing.intent import Intent


# Adjust this module path only if your LLMAgent
# is stored under a different filename.
llm_module = importlib.import_module(
    "Backend.Agents.llm_agent"
)


@pytest.fixture
def mock_llm(monkeypatch):

    # Avoid calling the real Ollama Cloud service.
    monkeypatch.setattr(
        llm_module,
        "generate_llm_response",
        lambda **kwargs: "Generated AI response"
    )

    # Mock the report prompt builder.
    monkeypatch.setattr(
        llm_module,
        "build_report_prompt",
        lambda state: "Test report prompt"
    )

    # Mock the conversation prompt builder.
    monkeypatch.setattr(
        llm_module,
        "build_conversation_prompt",
        lambda state: "Test conversation prompt"
    )

    # Mock output validation.
    monkeypatch.setattr(
        llm_module,
        "validate_llm_output",
        lambda response, intent: response
    )

    return llm_module.LLMAgent()


@pytest.mark.unit
def test_report_returns_correct_state_key(
    mock_llm,
    sample_state
):

    result = mock_llm.run(
        sample_state,
        Intent.REPORT
    )

    assert result == {
        "llm_report": "Generated AI response"
    }


@pytest.mark.unit
def test_chat_returns_correct_state_key(
    mock_llm,
    sample_state
):

    result = mock_llm.run(
        sample_state,
        Intent.CHAT
    )

    assert result == {
        "chat_response": "Generated AI response"
    }


@pytest.mark.unit
def test_llm_does_not_return_entire_state(
    mock_llm,
    sample_state
):

    result = mock_llm.run(
        sample_state,
        Intent.REPORT
    )

    assert "query" not in result

    assert "session_id" not in result

    assert "output_key" not in result


@pytest.mark.unit
def test_unsupported_llm_intent(
    mock_llm,
    sample_state
):

    with pytest.raises(
        ValueError,
        match="Unsupported intent"
    ):

        mock_llm.run(
            sample_state,
            "INVALID_INTENT"
        )