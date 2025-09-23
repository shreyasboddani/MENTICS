# 🧠 Mentics: Your AI-Powered Path to Success

<p align="center">
  <img alt="Python" src="https://img.shields.io/badge/Python-3.11+-blue?logo=python&logoColor=white">
  <img alt="Flask" src="https://img.shields.io/badge/Flask-3.0.0-black?logo=flask&logoColor=white">
  <img alt="Google Gemini" src="https://img.shields.io/badge/Google%20Gemini-AI%20Powered-blueviolet?logo=google&logoColor=white">
  <img alt="SQLite" src="https://img.shields.io/badge/SQLite-3-blue?logo=sqlite&logoColor=white">
  <img alt="TailwindCSS" src="https://img.shields.io/badge/Tailwind%20CSS-3-green?logo=tailwindcss&logoColor=white">
</p>

<p align="center">
  Mentics is a dynamic, full-stack web application built with Flask that acts as a personal AI mentor for high school students. It leverages the power of the Google Gemini API to create personalized, adaptive roadmaps for both standardized test preparation (SAT/ACT) and the comprehensive college planning process, helping students transform their ambitions into tangible achievements.
</p>

---

## ✨ Key Features

Mentics has evolved to become a holistic platform for student success, incorporating a wide range of features to guide, motivate, and connect users.

### Core AI & Path Generation
* **Dual-Focus AI Paths**: Mentics offers two distinct, AI-driven journeys:
    * **Test Prep**: Generates a tailored study plan based on desired scores, strengths, weaknesses, and test dates.
    * **College Planning**: Creates a step-by-step guide for college applications, essays, and research, adapted to the student's grade level and goals.
* **Interactive Path Visualization**: An elegant and intuitive UI allows students to visualize their journey, click on nodes for task details, mark tasks as complete, and see their progress in real-time.
* **Dynamic Path Regeneration**: The AI can regenerate a user's path at any time based on their conversational input with the AI assistant, ensuring the plan always aligns with their evolving needs.
* **AI-Powered Essay Analysis**: A dedicated tool provides in-depth, constructive feedback on college essays, analyzing clarity, voice, structure, and grammar to help students refine their writing.

### User Engagement & Support
* **AI Assistant Chat**: An integrated chat feature, powered by Gemini, allows students to get "unstuck" at any time. It provides help on specific tasks, offers strategic advice, and saves conversation history for a continuous, context-aware experience.
* **Custom Tasks & Subtasks**: In addition to AI-generated tasks, users can add their own custom tasks to their path and break down complex tasks into smaller, manageable subtasks.
* **Stats & Progress Tracking**: A comprehensive dashboard where users can log their GPA and test scores. The **Tracker** page provides detailed charts to visualize score progression and review a complete history of all past study plans.
* **Proactive AI Encouragement**: The dashboard features an "AI Encouragement" card that provides personalized, motivational messages based on the user's recent activity, stats, and goals.

### Community & Gamification
* **Community Forum**: A built-in forum allows users to start discussions, ask questions, and reply to each other, creating a supportive and collaborative community.
* **Gamification Engine**: To keep users motivated, Mentics includes:
    * **Points System**: Earn points for completing tasks, with bonus points for major "milestone" and "boss battle" tasks.
    * **Streaks**: Build and maintain a daily streak by completing at least one task each day.
    * **Achievements**: Unlock achievements for reaching key milestones, such as completing a certain number of tasks or maintaining a long streak.
* **Leaderboard**: A public leaderboard showcases the top users based on points earned, fostering a sense of friendly competition.

### Account & Authentication
* **Secure User Authentication**: Full support for user registration and login with both traditional email/password and seamless **Google OAuth 2.0**.
* **Comprehensive Account Management**: Users have a dedicated account page where they can:
    * Update their name, email, and password.
    * Upload and change their profile picture.

---

## 💻 Technology Stack

Mentics is built with a modern and robust technology stack:

* **Backend**: Python, Flask
* **Database**: SQLite
* **AI**: Google Gemini API (`google-generativeai`)
* **Authentication**: Werkzeug Security (for password hashing), Authlib (for Google OAuth)
* **Frontend**: HTML, Tailwind CSS, Vanilla JavaScript
* **Charting**: ApexCharts.js for dynamic and beautiful progress charts.

---

## 🚀 Getting Started

To get a local copy up and running, follow these simple steps.

### Prerequisites

* Python 3.9+
* An environment variable manager (like `python-dotenv`)
* Google Gemini API Key

### Installation

1.  **Clone the repository:**
    ```sh
    git clone (https://github.com/shreyasboddani/MENTICS)
    cd MENTICS
    ```
2.  **Create a virtual environment:**
    ```sh
    python -m .venv venv
    source .venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```
3.  **Install the dependencies:**
    ```sh
    pip install -r requirements.txt
    ```
4.  **Set up your environment variables:**
    Create a `.env` file in the root directory and add your Google Gemini API key:
    ```
    GEMINI_API_KEY='YOUR_API_KEY_HERE'
    GOOGLE_CLIENT_ID='YOUR_GOOGLE_CLIENT_ID'
    GOOGLE_CLIENT_SECRET='YOUR_GOOGLE_CLIENT_SECRET'
    ```
5.  **Initialize the database and run the application:**
    ```sh
    flask run
    ```
    The application will be available at `http://127.0.0.1:5000`.

---

## 👥 Contributors

* Shreyas Boddani
* Brandon Potter
