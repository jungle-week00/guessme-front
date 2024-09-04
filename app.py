from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient
import random

app = Flask(__name__)

# MongoDB 설정
client = MongoClient('localhost', 27017)
db = client.quizdb
user_collection = db.userdb

# 홈 페이지
@app.route('/')
def home():
  return render_template('index.html')

# 퀴즈 페이지
@app.route('/quiz')
def quiz():
  return render_template('quiz.html')

# 퀴즈 입력 폼
@app.route('/quizform')
def quiz_form():
  return render_template('quiz-form.html')

# 자기소개 입력 폼
@app.route('/introform')
def intro_form():
  return render_template('intro-form.html')

# 수정할 항목 선택 페이지
@app.route('/edit_selection')
def edit_selection():
    return render_template('edit-selection.html')

# 퀴즈 수정 페이지
@app.route('/edit_quiz/<int:quiz_number>')
def edit_quiz(quiz_number):
    return render_template('edit-quiz.html', quiz_number=quiz_number)

# 자기소개 수정 페이지
@app.route('/edit_intro')
def edit_intro():
    return render_template('edit-intro.html')

# API: 자기소개 생성
@app.route('/api/submit_intro/<string:user_id>', methods=['POST'])
def submit_intro(user_id):
    data = request.get_json()

    quizzes = data.get("quizzes")
    intro = data.get("intro")

    # 데이터 검증
    if not quizzes or len(quizzes) != 5:
        return jsonify({"message": "5개의 퀴즈를 보내야 합니다."}), 400
    if not intro:
        return jsonify({"message": "자기소개가 필요합니다."}), 400

    user = user_collection.find_one({"user_id": user_id})

    if not user:
        # 새 사용자 생성
        user_collection.insert_one({
            "user_id": user_id,
            "quizzes": quizzes,
            "intro": intro
        })
    else:
        # 기존 사용자 업데이트
        user_collection.update_one(
            {"user_id": user_id},
            {"$set": {
                "quizzes": quizzes,
                "intro": intro
            }}
        )

    return jsonify({'result': 'success'}), 201

# API: 퀴즈 불러오기
@app.route('/api/quiz/<string:user_id>', methods=['GET'])
def get_quiz_data(user_id):
    user = user_collection.find_one({"user_id": user_id})
    if not user or "quizzes" not in user:
        return jsonify({"message": "유저 또는 퀴즈를 찾을 수 없습니다."}), 404
    
    quiz_data = user["quizzes"][:5]
    for quiz in quiz_data:
        options = quiz['answer']['wrong'] + [quiz['answer']['correct']]
        random.shuffle(options)
        quiz['shuffled_options'] = options

    return jsonify(quiz_data), 200

# API: 모든 퀴즈 불러오기
@app.route('/quiz/<string:user_id>', methods=['GET'])
def get_all_quizzes(user_id):
    user = user_collection.find_one({"user_id": user_id})
    if not user:
        return jsonify({"message": "유저를 찾을 수 없습니다."}), 404

    return jsonify(user["quizzes"]), 200

# API: 특정 퀴즈 가져오기
@app.route('/quiz/<string:user_id>/<int:quiz_number>', methods=['GET'])
def get_quiz(user_id, quiz_number):
    user = user_collection.find_one({"user_id": user_id})
    if not user:
        return jsonify({"message": "유저를 찾을 수 없습니다."}), 404
    
    quiz = next((q for q in user["quizzes"] if q["number"] == quiz_number), None)
    if not quiz:
        return jsonify({"message": "퀴즈를 찾을 수 없습니다."}), 404
    
    return jsonify(quiz), 200

# API: 퀴즈 수정
@app.route('/api/quiz/<string:user_id>/<int:quiz_number>', methods=['PUT'])
def update_quiz(user_id, quiz_number):
    data = request.get_json()
    user = user_collection.find_one({"user_id": user_id})

    if not user:
        return jsonify({"message": "유저를 찾을 수 없습니다."}), 404
    
    quizzes = user.get("quizzes", [])
    quiz_index = next((i for i, q in enumerate(quizzes) if q["number"] == quiz_number), None)

    if quiz_index is None:
        return jsonify({"message": "퀴즈를 찾을 수 없습니다."}), 404

    # 퀴즈 업데이트
    quizzes[quiz_index] = data
    user_collection.update_one(
        {"user_id": user_id},
        {"$set": {"quizzes": quizzes}}
    )

    return jsonify({"message": "퀴즈가 업데이트되었습니다."}), 200

# API: 자기소개 불러오기
@app.route('/api/edit_intro/<string:user_id>', methods=['GET'])
def get_intro(user_id):
    user = user_collection.find_one({'user_id': user_id})
    if user and 'intro' in user:
        return jsonify({'intro': user['intro']}), 200
    else:
        return jsonify({'message': '자기소개를 찾을 수 없습니다.'}), 404

# API: 자기소개 수정
@app.route('/api/edit_intro/<string:user_id>', methods=['POST'])
def update_intro(user_id):
    data = request.get_json()
    intro = data.get('intro')

    user = user_collection.find_one({'user_id': user_id})
    if user:
        user_collection.update_one({'user_id': user_id}, {'$set': {'intro': intro}})
        return jsonify({'message': '자기소개가 성공적으로 수정되었습니다.'}), 200
    else:
        return jsonify({'message': '해당 유저를 찾을 수 없습니다.'}), 404

if __name__ == '__main__':
   app.run('0.0.0.0', port=5000, debug=True)
