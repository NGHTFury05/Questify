import sys
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QLineEdit
from sentence_transformers import SentenceTransformer
from pymongo import MongoClient

client = MongoClient('mongodb+srv://harissh:Xboxones07@cluster0.dm6mvwq.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0')
db = client['music'] 
collection = db['top50'] 
model = SentenceTransformer('all-MiniLM-L6-v2')

#embedding generator for the attributes
"""for doc in collection.find():
    doc_string = create_document_string(doc)
    embedding = model.encode(doc_string).tolist()
    collection.update_one({'_id': doc['_id']}, {'$set': {'embedding': embedding}})"""

class MusicManagerApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Music Manager')
        self.setGeometry(100, 100, 400, 300)
        self.label = QLabel('Welcome to Music Manager', self)
        self.label.setAlignment(Qt.AlignCenter)
        self.query_text_field = QLineEdit(self)
        self.query_text_field.setPlaceholderText("Enter your query")
        self.response_label = QLabel(self)
        self.response_label.setAlignment(Qt.AlignCenter)
        self.get_response_button = QPushButton('Get Response', self)
        self.get_response_button.clicked.connect(self.get_response_button_clicked)
        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.query_text_field)
        layout.addWidget(self.response_label)
        layout.addWidget(self.get_response_button)
        self.setLayout(layout)

    def get_response_button_clicked(self):
        user_query = self.query_text_field.text()
        print(user_query)
        response = self.generate_response(user_query)
        self.response_label.setText(response)
    
    def create_document_string(self,doc):
        fields = ['Track.Name', 'Artist.Name', 'Genre', ]
        document_string = " ".join(str(doc[field]) for field in fields if field in doc)
        return document_string

    def generate_response(self, user_query):
        query_embedding = model.encode(user_query).tolist()
        results=collection.aggregate([

            {
                "$vectorSearch": {
                "index": "vector_index",
                "path": "embedding",
                "queryVector": query_embedding,
                "numCandidates": 50,
                "limit":5               
                }
            }
        ])
        try:
            top_docs = list(results)
            res = "\n\n".join([self.create_document_string(doc) for doc in top_docs])
            return res if res else "No relevant documents found."
        except Exception as e:
            print(f"Error performing vector search: {e}")
            return "Error: Unable to perform search."
            
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MusicManagerApp()
    window.show()
    sys.exit(app.exec_()) 

