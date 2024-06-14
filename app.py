import dash
from dash import dcc, html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
import plotly.express as px
from collections import Counter
from utils import loadCsv, insert_line_breaks

csv_files = {
    '/season1': 'season1.csv',
    '/season2': 'season2.csv',
    '/season3': 'season3.csv'
}

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)
server = app.server

def load_questions(pathname):
    if pathname in csv_files:
        return loadCsv(csv_files[pathname])
    return None

color_mapping = {}

def generate_color(index):
    hex_color = px.colors.qualitative.Light24[index][1:]
    rgb = list(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    return 'rgb({}, {}, {})'.format(rgb[0], rgb[1], rgb[2])

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
                    dcc.Graph(id='pie-chart', style={"display": "inline-block"}),
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
    [Output('pie-chart', 'figure'),
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
        return go.Figure(), current_question_index, [], None

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

    global color_mapping

    for answer_obj in question.answers:
        answer = answer_obj.answer
        respondent = answer_obj.answered_by

        if answer not in answer_count:
            answer_count[answer] = 0
            answer_respondents[answer] = []

        answer_count[answer] += 1
        answer_respondents[answer].append(respondent)

        if answer not in color_mapping:
            color_mapping[answer] = generate_color(len(color_mapping))

    answer_labels = list(answer_count.keys())
    answer_values = list(answer_count.values())
    answer_texts = [f"{', '.join(respondents)}" for respondents in answer_respondents.values()]

    marker_colors = [color_mapping[label] for label in answer_labels]

    fig = go.Figure(data=[
        go.Pie(
            labels=answer_labels,
            values=answer_values,
            hovertext=answer_texts,
            hoverinfo='text',
            textinfo='label+percent',
            marker=dict(colors=marker_colors)
        )
    ])
    
    wrapped_title = insert_line_breaks(question.name)
    
    fig.update_layout(
        title={
            'text': f'{wrapped_title}',
            'x': 0.5, 
            'xanchor': 'center', 
            'yanchor': 'top'
        },
        hovermode='x unified',
        autosize=True,
        width=600,
        height=500,
        margin=dict(l=50, r=50, t=70, b=50),
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.1,
            xanchor="center",
            x=0.5
        )
    )

    return fig, new_index, question_labels, new_index

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

    all_answers = [answer_obj.answer for question in questions for answer_obj in question.answers]

    if not all_answers:
        return "No answers available."

    answer_counter = Counter(all_answers)

    most_mentioned = answer_counter.most_common(1)[0]
    least_mentioned = answer_counter.most_common()[-1]

    self_votes = Counter()
    specific_votes = Counter()

    all_answers_by_person = {}
    for question in questions:
        for answer in question.answers:
            respondent = answer.answered_by
            response = answer.answer

            if respondent not in all_answers_by_person:
                all_answers_by_person[respondent] = []
            all_answers_by_person[respondent].append(response)

            if respondent == response:
                self_votes[respondent] += 1

            if respondent != response:
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
    app.run_server(port=8080)