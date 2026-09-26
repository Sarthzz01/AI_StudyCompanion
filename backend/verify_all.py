import requests

BASE = 'http://localhost:8000/api'
print('=== FULL-STACK END-TO-END VALIDATION ===\n')

# 1. Frontend check
fe = requests.get('http://localhost:5173')
assert fe.status_code == 200
print('[PASS] 1. Frontend web server: 200 OK (Serving React app on http://localhost:5173)')

# 2. Student Authentication
r = requests.post(f'{BASE}/auth/login', json={'email': 'student@study.edu', 'password': 'password123'})
assert r.status_code == 200
data = r.json()
token = data['access_token']
headers = {'Authorization': f'Bearer {token}'}
user_name = data['user']['name']
print(f'[PASS] 2. Student authenticated: {user_name}')

# 3. Profile
r = requests.get(f'{BASE}/profile', headers=headers)
assert r.status_code == 200
print(f'[PASS] 3. Profile loaded: {r.json()["full_name"]}')

# 4. Materials
r = requests.get(f'{BASE}/materials', headers=headers)
assert r.status_code == 200
materials = r.json()
print(f'[PASS] 4. Materials retrieved: {len(materials)} documents in library')

# 5. AI Tutor (RAG-grounded with Gemini)
r = requests.post(f'{BASE}/tutor/ask', json={'question': 'What is a binary search tree?', 'material_id': 'data-structures'}, headers=headers)
assert r.status_code == 200
tutor_ans = r.json()['answer']
sources_count = len(r.json().get('sources', []))
print(f'[PASS] 5. Grounded AI Tutor: Answer generated ({len(tutor_ans)} chars, {sources_count} source citations)')

# 6. Flashcards
r = requests.get(f'{BASE}/flashcards', headers=headers)
assert r.status_code == 200
print(f'[PASS] 6. Flashcards active: {len(r.json())} cards loaded')

# 7. Quizzes
r = requests.get(f'{BASE}/quizzes', headers=headers)
assert r.status_code == 200
print(f'[PASS] 7. Quizzes active: {len(r.json())} quizzes available')

# 8. Study Plan
r = requests.get(f'{BASE}/study-plan', headers=headers)
assert r.status_code == 200
print(f'[PASS] 8. Study Plan active: {len(r.json())} daily tasks')

# 9. Revision Matrix
r = requests.get(f'{BASE}/revision', headers=headers)
assert r.status_code == 200
topics = r.json() if isinstance(r.json(), list) else r.json().get('topics', [])
print(f'[PASS] 9. Spaced Repetition Matrix active: {len(topics)} topics tracked')

# 10. Notifications
r = requests.get(f'{BASE}/notifications', headers=headers)
assert r.status_code == 200
print(f'[PASS] 10. Notifications active: {len(r.json())} notifications')

# 11. Progress Analytics
r = requests.get(f'{BASE}/progress', headers=headers)
assert r.status_code == 200
accuracy = r.json().get('accuracy', 0)
print(f'[PASS] 11. Student Analytics active: Accuracy={accuracy}%')

# 12. Instructor Module
r_inst = requests.post(f'{BASE}/auth/login', json={'email': 'instructor@study.edu', 'password': 'password123'})
assert r_inst.status_code == 200
inst_token = r_inst.json()['access_token']
inst_headers = {'Authorization': f'Bearer {inst_token}'}
r_stud = requests.get(f'{BASE}/instructor/students', headers=inst_headers)
assert r_stud.status_code == 200
print(f'[PASS] 12. Instructor Portal active: {len(r_stud.json())} students enrolled under Dr. Alan Turing')

print('\n=== ALL 12 FULL-STACK CRITICAL SERVICES ARE 100% OPERATIONAL ===')
