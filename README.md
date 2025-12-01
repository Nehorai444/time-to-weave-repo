# time-to-weave-repo
Time to Weave

Time to Weave — A full-stack online course platform built for adults (age 60+), focusing on accessible, Zoom-based classes (e.g. knitting, crafts), with multilingual support (Hebrew, English, Spanish) and a clean, user-friendly UI.

🚀 What is this?

Time to Weave is a web application for connecting older adults (and people with mobility limitations) with online courses taught through Zoom.
The platform is designed to be easy to use, accessible, and welcoming — helping seniors participate in creative/group activities, learn new skills, stay socially engaged and connected, all from the comfort of home.

📚 Key Features

Full-stack architecture: backend in Python Flask + MySQL, frontend in Vue.js with Quasar Framework.

Multi-language support: Hebrew, English, Spanish.

Accessibility features and dark mode support.

User dashboard showing: account balance (in ILS), monthly spend, enrolled courses, course progress, recommended courses, course cost overlay, etc.

Profile page designed like a social-app profile, showing courses taken instead of “friends/groups”.

Flexible registration: users register per course; pricing: 240 NIS per course, 35 NIS trial session.

Instructor workflow: instructors can be sourced (e.g. via Facebook) or via open application in the future.

Modular backend design: separate route files (auth, feedback, admin, course registration, Zoom-session handling, etc.).

📦 Repo Structure
/backend        — Flask backend (MySQL, .env config)
/frontend       — Vue.js + Quasar frontend
/load-data      — (optional) scripts/tools for loading data (if any)
README.md       — this file

🛠️ Getting Started (Local Setup)

Ensure you have Python, Node.js / npm installed.

Clone the repository

git clone https://github.com/Nehorai444/time-to-weave-repo.git
cd time-to-weave-repo


Backend setup

cd backend
# Create .env (with DB credentials, etc.)
# Install dependencies:
pip install -r requirements.txt
# Run migrations / ensure MySQL database is ready
# Start the Flask server:
flask run


Frontend setup

cd ../frontend
npm install
npm run dev  # or the Quasar dev command you configured


Open your browser and navigate to http://localhost:xxxx (as configured) to use the app.

(You may also need to setup Zoom-related env variables/keys, depending on your Zoom integration.)

🤝 Contributing

Interested in contributing? Great! Here’s how:

Fork the repo.

Create a branch for your feature/fix.

Commit your changes with clear messages.

Submit a Pull Request.

Please make sure to follow the existing project structure (modular backend, separate route-files, etc.) and add translations via vue-i18n when adding UI elements.

💡 Why it matters / Who it’s for

Time to Weave was built with the goal of empowering older adults, especially those who are home-bound or have mobility limitations — helping them stay socially connected, learn new skills, and enjoy group learning without needing to physically leave home. The platform aims to be accessible, easy to navigate, and inclusive.

For developers or collaborators: this is a “real-world” full-stack project: modern frontend (Vue + Quasar), backend (Flask + MySQL), modular code structure, and support for multi-language + accessibility. Good for expanding, customizing, or building on top.

📧 Contact

For questions, ideas, or feedback — reach out to: levinehorai1@gmail.com
 (project creator / maintainer)

📝 License

(You can choose a license — e.g. MIT — and add it here.)
