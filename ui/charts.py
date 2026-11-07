"""Plotly charts used on the Results page."""

import plotly.graph_objects as go

from ui.styles import AMBER, NAVY, TEAL, CORAL, SKY

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
PALETTE = [AMBER, NAVY, TEAL, SKY, CORAL, "#8E7DBE", "#9CA3AF"]


def _base_layout(fig, title, height=360):
    fig.update_layout(
        title=dict(text=title, font=dict(size=15, color=NAVY)),
        height=height,
        margin=dict(l=10, r=10, t=50, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5),
        font=dict(color="#374151"),
    )
    return fig


def cost_breakdown(breakdown):
    fig = go.Figure(go.Pie(
        labels=list(breakdown.keys()),
        values=list(breakdown.values()),
        hole=0.55,
        marker=dict(colors=PALETTE[:len(breakdown)]),
        textinfo="percent",
        hovertemplate="%{label}<br>Rs %{value:,.0f}<extra></extra>",
    ))
    return _base_layout(fig, "Where the money goes", height=380)


def cashflow(values):
    years = list(range(len(values)))
    colors = [CORAL if v < 0 else TEAL for v in values]
    fig = go.Figure(go.Bar(
        x=years, y=values, marker_color=colors,
        hovertemplate="Year %{x}<br>Rs %{y:,.0f}<extra></extra>",
    ))
    fig.add_hline(y=0, line_dash="dash", line_color=NAVY)
    fig.update_xaxes(title_text="Year")
    fig.update_yaxes(title_text="Cumulative cash position (Rs)", tickformat=",.0f")
    return _base_layout(fig, "Cumulative savings after investment (bars turn green after payback)")


def monthly_energy(daily_kwh, daily_gen, solar_factors, use_factors):
    days = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    use = [round(daily_kwh * f * d) for f, d in zip(use_factors, days)]
    gen = [round(daily_gen * f * d) for f, d in zip(solar_factors, days)]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=MONTHS, y=use, name="Consumption (kWh)", marker_color=NAVY))
    fig.add_trace(go.Bar(x=MONTHS, y=gen, name="Solar generation (kWh)", marker_color=AMBER))
    fig.update_layout(barmode="group")
    fig.update_yaxes(title_text="kWh per month")
    return _base_layout(fig, "Estimated monthly consumption vs solar generation")


def appliance_energy(breakdown):
    items = sorted(breakdown.items(), key=lambda kv: kv[1])
    fig = go.Figure(go.Bar(
        x=[v for _, v in items], y=[k for k, _ in items], orientation="h",
        marker_color=AMBER, hovertemplate="%{y}: %{x:.2f} kWh/day<extra></extra>",
    ))
    fig.update_xaxes(title_text="kWh per day")
    return _base_layout(fig, "Daily energy by appliance (from your list)", height=max(260, 34 * len(items) + 90))


def coverage_gauge(percent):
    value = min(percent, 150)
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        number=dict(suffix="%", font=dict(color=NAVY)),
        gauge=dict(
            axis=dict(range=[0, 150]),
            bar=dict(color=AMBER),
            steps=[dict(range=[0, 50], color="#FDECEA"),
                   dict(range=[50, 90], color="#FFF1D6"),
                   dict(range=[90, 150], color="#E3F4F1")],
        ),
    ))
    return _base_layout(fig, "Solar coverage of daily usage", height=280)
