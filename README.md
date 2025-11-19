# 📘 CodeAdventure 
CodeAdventure is a web platform supporting online programming training. The main purpose is to provide a structured, accessible, and engaging environment where learners can gradually develop their programming skills. 
## 🚀 Key Features
### Group: Core
- ✅ **Register /  Log in**
  - **Description:** Allows users to create an account and log in.
  - **Usage:** `/api/v1/auth/register/`
  - **Requirements:** Password encryption using JWT.
- ✅ **Quiz attempt**
  - **Description:** Take quiz and get score after finishing.
  - **Example:** `/api/v1/quiz/<uuid:lesson_id>/attempts/`
- ✅ **Online code judging**
  - **Description:** Judge submitted code automatically.
  - **Example:** `GET /api/lessons/` returns a paginated list.
### Group: Admin
- ✅ **Admin Dashboard**
  - **Description:** View user's statistics, lessons, logs and manage users (CRUD user).
  - **How to access:** /admin (role=admin)
- ✅ **Course Management (CRUD Course)**
  - **Description:** Create, Read, Update, and Delete lessons.
  - **Example:** `GET /api/v1/courses/` returns a paginated list.
  - **Note:** Create/Update/Delete permissions are restricted to the `admin` role.  
- ✅ **Quiz Management (CRUD Quiz)**
  - **Description:** Create, Read, Update, and Delete Quiz.
  - **Example:** `GET /api/v1/quizzes/` returns a paginated list.
  - **Note:** Create/Update/Delete permissions are restricted to the `admin` role. 
## 💻 Tech Stacks
* **Frontend:** ReactJS, HTML, CSS
* **Backend:** Django
* **Database:** PostgreSQL
## 🛠️ Installation
### Requirements
- Python >= 3.10
- Django >= 4.0
- Node.js >= 18
### How to install
```bash
git clone https://github.com/codeadventure-web/codeadventure-backend.git
cd codeadventure-backend
pip install -r requirements.txt
python manage.py runserver
