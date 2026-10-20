from cong_agent.tools.utils.format import index_list, num, window_note


def test_num_rounds_floats_only():
    assert num(3.14159) == "3.14"
    assert num(7) == "7"


def test_window_note():
    assert window_note(19, 19) == ""
    assert "20–49" in window_note(19, 49)


def test_index_list_truncates_at_50():
    out = index_list(list(range(60)))
    assert "49" in out and "50," not in out and "처음 50개" in out
