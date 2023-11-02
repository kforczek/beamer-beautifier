from src.beamer.generator import ListToTable


def test_ListToTable_improve():
    ltt = ListToTable(r"\begin{enumerate}", r"\end{enumerate}")
    code = r"""
    \begin{enumerate}
        \item some item 1
        \item some item 2
        \item some item 3
    \end{enumerate}
    """

    improved_code = ltt.improve(code)
    expected_code = r"""
    \begin{tabular}{ccc}
     some item 1
      & some item 2
       & some item 3
       
    \end{tabular}
    """
    assert improved_code == expected_code
