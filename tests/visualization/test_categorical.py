import matplotlib
import pandas as pd
import warnings

matplotlib.use("Agg")

from cumcm2022c.visualization.categorical import (
    plot_association_heatmaps,
    plot_category_counts,
    plot_weathering_proportions,
)


def test_categorical_plots_return_expected_axes_without_mutating_data() -> None:
    frame = pd.DataFrame(
        {
            "纹饰": ["A", "B", "A", "B"],
            "类型": ["高钾", "高钾", "铅钡", "铅钡"],
            "颜色": ["蓝", "未知", "蓝", "绿"],
            "表面风化": ["无风化", "风化", "风化", "无风化"],
        }
    )
    original = frame.copy(deep=True)
    columns = frame.columns.tolist()
    identity = pd.DataFrame(1.0, index=columns, columns=columns)
    reliable = pd.DataFrame(True, index=columns, columns=columns)

    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always")
        count_figure, count_axes = plot_category_counts(frame, columns)
        heat_figure, heat_axes = plot_association_heatmaps(identity, identity, reliable)
        weather_figure, weather_axes = plot_weathering_proportions(
            frame, ["纹饰", "类型", "颜色"]
        )
        for figure in (count_figure, heat_figure, weather_figure):
            figure.canvas.draw()

    assert len(count_axes.flat) == 4
    assert len(heat_axes.flat) == 2
    assert len(weather_axes.flat) == 3
    pd.testing.assert_frame_equal(frame, original)
    assert not [warning for warning in captured if "Glyph" in str(warning.message)]
