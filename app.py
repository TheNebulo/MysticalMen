import dash
from dash import dcc, html, dash_table
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
import plotly.express as px
from collections import Counter
from utils import loadCsv, insert_line_breaks

MAX_UNIQUE_ANSWERS = 10

csv_files = {
    '/season1': 'season1.csv',
    '/season2': 'season2.csv',
    '/season3': 'season3.csv',
    '/season4': 'season4.csv'
}

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)
server = app.server

def load_questions(pathname):
    if pathname in csv_files:
        return loadCsv(csv_files[pathname])
    return None

color_mapping = {}

def generate_color(index):
    palette = px.colors.qualitative.Light24
    valid_index = index % len(palette)
    hex_color = palette[valid_index].lstrip('#')
    r, g, b = (int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    return f'rgb({r}, {g}, {b})'

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])

home_page_layout = html.Div([
    dbc.Container([
        dbc.Row([
            dbc.Col(
                html.H2("Mystical Men Results", style={"word-wrap": "break-word", "white-space": "normal"}),
                className="text-center mb-5 mt-5"
            )
        ]),
        dbc.Row([
            dbc.Col(
                html.Div([
                    dbc.Button("Go to Season 1", href="/season1", color="primary", className="mx-2 mb-2"),
                    dbc.Button("Go to Season 2", href="/season2", color="success", className="mx-2 mb-2"),
                    dbc.Button("Go to Season 3", href="/season3", color="warning", className="mx-2 mb-2"),
                    dbc.Button("Go to Season 4", href="/season4", color="info", className="mx-2 mb-2"),
                ], className="text-center")
            )
        ])
    ])
])

def generate_results_layout(season_title):
    return html.Div([
        dbc.Container([
            dbc.Row([
                dbc.Col(
                    html.H2(f"Mystical Men Results - {season_title}", className="text-center", style={"word-wrap": "break-word", "white-space": "normal"}),
                    className="mb-5 mt-5"
                )
            ]),
            dbc.Row([
                dbc.Col(
                    html.Div(id='chart-or-table', style={"text-align": "center"}),
                    style={"text-align": "center"}
                )
            ]),
            dbc.Row([
                dbc.Col(
                    html.Div([
                        dcc.Dropdown(id='question-dropdown', style={"width": "50%", "margin": "auto", "word-wrap": "break-word", "white-space": "normal"}, className="custom-dropdown mb-2", placeholder="", clearable=False),
                        dbc.Button('Show Statistics', id='show-stats-button', n_clicks=0, color="info", className="mx-2 mb-2"),
                        dbc.Button('Previous', id='previous-button', n_clicks=0, color="primary", className="mx-2 mb-2"),
                        dbc.Button('Next', id='next-button', n_clicks=0, color="success", className="mx-2 mb-2"),
                    ], className="text-center")
                )
            ]),
            dcc.Store(id='current-question-index', data=0)
        ]),
        html.Div(id="footer", className="text-center mt-5"),

        dbc.Modal(
            [
                dbc.ModalHeader("Key Statistics"),
                dbc.ModalBody(id="statistics-body"),
                dbc.ModalFooter(
                    dbc.Button("Close", id="close-stats-button", className="ml-auto")
                )
            ],
            id="stats-modal",
            is_open=False,
        ),
    ])

@app.callback(
    Output('page-content', 'children'),
    Input('url', 'pathname')
)
def display_page(pathname):
    global color_mapping
    color_mapping = {}
    
    if pathname == '/' or pathname not in csv_files and pathname != '/':
        return home_page_layout  # Remove the parentheses
    elif pathname in csv_files:
        season_title = pathname.strip('/').capitalize()
        season_title = season_title[:-1] + " " + season_title[-1]
        return generate_results_layout(season_title)
    else:
        return dcc.Location(href='/', id='redirect-to-home')


@app.callback(
    [Output('chart-or-table', 'children'),
     Output('current-question-index', 'data'),
     Output('question-dropdown', 'options'),
     Output('question-dropdown', 'value')],
    [Input('url', 'pathname'),
     Input('previous-button', 'n_clicks'),
     Input('next-button', 'n_clicks'),
     Input('question-dropdown', 'value')],
    [State('current-question-index', 'data')]
)
def update_graph(pathname, prev_clicks, next_clicks, dropdown_value, current_question_index):
    questions = load_questions(pathname)

    if not questions:
        return html.Div("No data available."), current_question_index, [], None

    question_labels = [{'label': q.name, 'value': i} for i, q in enumerate(questions)]

    ctx = dash.callback_context
    if not ctx.triggered:
        button_id = 'No clicks yet'
    else:
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if button_id == 'previous-button' and current_question_index > 0:
        new_index = current_question_index - 1
    elif button_id == 'next-button' and current_question_index < len(questions) - 1:
        new_index = current_question_index + 1
    elif button_id == 'question-dropdown' and dropdown_value is not None:
        new_index = dropdown_value
    else:
        new_index = current_question_index

    question = questions[new_index]

    answer_count = {}
    answer_respondents = {}
    color_mapping = {}
    
    unique_answers = sorted(set(ans.answer for ans in question.answers))
    for idx, answer in enumerate(unique_answers):
        color_mapping[answer] = generate_color(idx)

    for answer_obj in question.answers:
        answer = answer_obj.answer
        respondent = answer_obj.answered_by

        answer_count.setdefault(answer, 0)
        answer_respondents.setdefault(answer, [])

        answer_count[answer] += 1
        answer_respondents[answer].append(respondent)

    answer_labels = list(answer_count.keys())
    answer_values = list(answer_count.values())
    answer_texts = [f"{', '.join(respondents)}" for respondents in answer_respondents.values()]
    marker_colors = [color_mapping[label] for label in answer_labels]

    wrapped_title = insert_line_breaks(question.name)

    if len(answer_count) <= MAX_UNIQUE_ANSWERS:
        short_labels = [label if len(label) <= 15 else label[:12] + "..." for label in answer_labels]
        
        fig = go.Figure(data=[
            go.Pie(
                labels=short_labels,
                values=answer_values,
                hovertext=answer_texts,
                hoverinfo='text',
                textinfo='label+percent',
                marker=dict(colors=marker_colors)
            )
        ])
        fig.update_layout(
            title={'text': f'{wrapped_title}', 'x': 0.5, 'xanchor': 'center'},
            width=600,
            height=500,
            margin=dict(l=50, r=50, t=70, b=50),
            legend=dict(orientation="h", yanchor="top", y=-0.1, xanchor="center", x=0.5)
        )
        chart_or_table = dcc.Graph(figure=fig, style={"display": "inline-block"})
    else:
        table_data = [
            {"Answer": ans, "Count": answer_count[ans], "Respondents": ", ".join(answer_respondents[ans])}
            for ans in answer_labels
        ]
        chart_or_table = dash_table.DataTable(
            columns=[
                {"name": "Answer", "id": "Answer"},
                {"name": "Count", "id": "Count"},
                {"name": "Respondents", "id": "Respondents"}
            ],
            data=table_data,
            style_table={"overflowX": "auto", "maxHeight": "500px", "overflowY": "auto", "margin": "auto", "width": "90%"},
            style_cell={"textAlign": "left", "whiteSpace": "normal", "height": "auto"},
        )

    return chart_or_table, new_index, question_labels, new_index

@app.callback(
    Output("stats-modal", "is_open"),
    [Input("show-stats-button", "n_clicks"), Input("close-stats-button", "n_clicks")],
    [State("stats-modal", "is_open")]
)
def toggle_modal(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open

@app.callback(
    Output("statistics-body", "children"),
    [Input('url', 'pathname')]
)
def update_statistics_body(pathname):
    questions = load_questions(pathname)

    if not questions:
        return "No data available."
    
    respondents = set()
    for question in questions:
        for answer in question.answers:
            if answer.answered_by:
                respondents.add(answer.answered_by)
    
    filtered_answers = []
    for question in questions:
        for answer in question.answers:
            if answer.answer in respondents:
                filtered_answers.append(answer)

    if not filtered_answers:
        return "No valid answers available."

    all_answers = [answer.answer for answer in filtered_answers]

    answer_counter = Counter(all_answers)

    most_mentioned = answer_counter.most_common(1)[0]
    least_mentioned = answer_counter.most_common()[-1]

    self_votes = Counter()
    specific_votes = Counter()

    all_answers_by_person = {}
    for answer in filtered_answers:
        respondent = answer.answered_by
        response = answer.answer

        if respondent not in all_answers_by_person:
            all_answers_by_person[respondent] = []
        all_answers_by_person[respondent].append(response)

        if respondent == response:
            self_votes[respondent] += 1
        else:
            specific_votes[(respondent, response)] += 1

    most_self_votes = self_votes.most_common(1)
    least_self_votes = self_votes.most_common()[-1] if self_votes else ("", 0)
    specific_most_votes = specific_votes.most_common(1)[0] if specific_votes else (("",""), 0)

    stat_elements = [
        html.P(f"Most Popular: {most_mentioned[0]} with {most_mentioned[1]} mentions."),
        html.P(f"Least Popular: {least_mentioned[0]} with {least_mentioned[1]} mentions."),
        html.P(f"Self-glazer: {most_self_votes[0][0]} voted for himself {most_self_votes[0][1]} times."),
        html.P(f"Selfless: {least_self_votes[0]} voted for himself only {least_self_votes[1]} time(s)."),
        html.P(f"Gay couple: {specific_most_votes[0][0]} voted for {specific_most_votes[0][1]} {specific_most_votes[1]} times."),
    ]

    return stat_elements

if __name__ == '__main__':
    app.title = "Mystical Men"
    app.run(host='0.0.0.0', port=5000)