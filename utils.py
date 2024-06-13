nicknames = {
    "season2.csv" : {
        "7 ft South African who is behind your eyes": "Liam",
        "Farranoushka": "Farran",
        "Nigger": "Minhyeok",
        "Tired": "Duval",
        "Yes": "Auke",
        "I am alpharius (This may be a lie)": "Jelmer"
    },
    "season3.csv" : {
        "KFC_watermelon_Lover": "Manthan",
        "Saturo Gojo (aka Farran)": "Farran",
        "Mnux": "Liam",
        "chris (2v1 me)": "Christofor",
        "Gojo": "Marco",
        "Casi": "Casimir",
        "Min": "Minhyeok"
    }
}

class Answer:
    def __init__(self, question, answer, answered_by):
        self.question = question
        self.answer = answer
        self.answered_by = answered_by

class Question:
    def __init__(self, name):
        self.name = name
        self.answers  = []
        
    def add_answer(self, answer, answered_by):
        self.answers.append(Answer(self, answer, answered_by))

def loadCsv(csv_path):
    with open(csv_path, 'r') as csv:
        lines = csv.readlines()
        
    question_names = lines[0].split(',')
    questions = [Question(question_name.strip()) for question_name in question_names[2:]]
    
    if len(lines) <= 1:
        return questions
    
    for line in lines[1:]:
        fields = line.split(',')
        
        name = fields[1].strip()
        
        if csv_path in nicknames.keys():
            if name in nicknames[csv_path].keys(): name = nicknames[csv_path][name]
        
        fields = fields[2:]
        
        for i, answer in enumerate(fields):
            questions[i].add_answer(answer.strip(), name.strip())
    
    return questions