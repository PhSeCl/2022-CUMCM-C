import pandas as pd
import pytest

from cumcm2022c.analysis.categorical import (
    association_matrix,
    cramers_v_bias_corrected,
    pairwise_categorical_associations,
    prepare_categorical_data,
)


def test_prepare_categorical_data_marks_missing_without_mutating_input() -> None:
    frame = pd.DataFrame({"颜色": ["蓝", None], "类型": ["高钾", "铅钡"]})

    result = prepare_categorical_data(frame, ["颜色", "类型"])

    assert result.to_dict(orient="records") == [
        {"颜色": "蓝", "类型": "高钾"},
        {"颜色": "未知", "类型": "铅钡"},
    ]
    assert pd.isna(frame.loc[1, "颜色"])


def test_cramers_v_is_one_for_identical_balanced_binary_variables() -> None:
    table = pd.DataFrame([[20, 0], [0, 20]])

    assert cramers_v_bias_corrected(table) == pytest.approx(1.0)


def test_cramers_v_is_zero_for_independent_balanced_variables() -> None:
    table = pd.DataFrame([[10, 10], [10, 10]])

    assert cramers_v_bias_corrected(table) == pytest.approx(0.0)


def test_pairwise_associations_cover_six_pairs_and_flag_sparse_tables() -> None:
    frame = pd.DataFrame(
        {
            "纹饰": ["A", "A", "B", "B", "C", "C"],
            "类型": ["高钾", "铅钡", "高钾", "铅钡", "高钾", "铅钡"],
            "颜色": ["c1", "c2", "c3", "c4", "c5", "c6"],
            "表面风化": ["无风化", "风化", "无风化", "风化", "无风化", "风化"],
        }
    )
    columns = ["纹饰", "类型", "颜色", "表面风化"]

    result = pairwise_categorical_associations(frame, columns)

    assert len(result) == 6
    assert set(result.columns) == {
        "variable_1",
        "variable_2",
        "n",
        "chi2",
        "dof",
        "p_value",
        "cramers_v",
        "min_expected",
        "low_expected_ratio",
        "chi_square_reliable",
    }
    color_rows = result[(result["variable_1"] == "颜色") | (result["variable_2"] == "颜色")]
    assert not color_rows["chi_square_reliable"].any()


def test_association_matrix_is_symmetric_with_expected_diagonal() -> None:
    frame = pd.DataFrame({"a": ["x", "x", "y", "y"], "b": ["u", "u", "v", "v"], "c": ["m"] * 4})
    columns = ["a", "b", "c"]
    results = pairwise_categorical_associations(frame, columns)

    matrix = association_matrix(results, columns, "cramers_v")

    assert matrix.equals(matrix.T)
    assert matrix.values.diagonal().tolist() == [1.0, 1.0, 1.0]
