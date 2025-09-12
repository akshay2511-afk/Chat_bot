# 🏛️ PAN & TAN ChatBot Assistant

A comprehensive multilingual chatbot system designed to assist users with PAN (Permanent Account Number) and TAN (Tax Deduction Account Number) related queries in both English and Hindi. The system integrates FastAPI backend with Rasa NLU for intelligent conversation handling.

## 🚀 Features

### Core Functionality
- **Multilingual Support**: English and Hindi language support
- **PAN Assistance**: Complete information about PAN applications, documents, and procedures
- **TAN Assistance**: Comprehensive TAN-related guidance and support
- **Phone Number Verification**: OTP-based verification system (currently disabled)
- **Consent Management**: GDPR-compliant data processing consent system
- **Session Management**: Token-based session control with conversation history
- **Real-time Chat**: Web-based chat interface with modern UI

### Technical Features
- **FastAPI Backend**: High-performance async API framework
- **Rasa NLU Integration**: Advanced natural language understanding
- **PostgreSQL Database**: Robust data storage with SQLAlchemy ORM
- **Responsive Web Interface**: Modern chat widget with consent banners
- **RESTful API**: Well-structured API endpoints for all operations

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   FastAPI       │    │   Rasa Bot      │
│   (HTML/JS)     │◄──►│   Backend       │◄──►│   (NLU Engine)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   PostgreSQL    │
                       │   Database      │
                       └─────────────────┘
```

## 📋 Prerequisites

- Python 3.8+
- PostgreSQL 12+
- Node.js (for Rasa)
- Git

## 🛠️ Installation

### 1. Clone the Repository
```bash
git clone <repository-url>
cd ChatBot_PAN2.o
```

### 2. Set Up Virtual Environment
```bash
python -m venv pan_env
source pan_env/bin/activate  # On Windows: pan_env\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Set Up Database
Create a PostgreSQL database named `PAN`:
```sql
CREATE DATABASE PAN;
```

Update the database connection in `backend/core/config.py` if needed:
```python
database_url: str = "postgresql://username:password@localhost:5432/PAN"
```

### 5. Install Rasa Dependencies
```bash
cd rasa_bot
pip install rasa
```

## 🚀 Running the Application

The application requires **4 terminals** to run all components:

### Terminal 1: Train Rasa Model
```bash
cd rasa_bot
rasa train
```

### Terminal 2: Start Rasa Actions Server
```bash
cd rasa_bot
rasa run actions --actions rasa_bot.actions.actions --port 5055
```

### Terminal 3: Start Rasa Server
```bash
cd rasa_bot
rasa run --enable-api --cors "*" --port 5005
```

### Terminal 4: Start FastAPI Application
```bash
cd ChatBot_PAN2.o
uvicorn app:app --reload --port 8000
```

### Access the Application
- **Web Interface**: Open `chat.html` in your browser or visit `http://localhost:8000`
- **API Documentation**: Visit `http://localhost:8000/docs` for Swagger UI

## 📱 Usage

### Web Interface
1. Open the chat interface by clicking the chat button
2. Provide your phone number when prompted
3. Select your preferred language (English/Hindi)
4. Choose from the available assistance options:
   - PAN assistance
   - TAN assistance
   - General assistance
   - Schedule callback
   - Feedback

### API Endpoints

#### Chat Endpoints
- `POST /chat` - Send messages to the chatbot
- `POST /chat/release` - Release session token
- `GET /health` - Health check

#### OTP Endpoints (Currently Disabled)
- `POST /api/otp/generate` - Generate OTP
- `POST /api/otp/verify` - Verify OTP
- `GET /api/otp/status/{phone_number}` - Check OTP status

#### Consent Management
- `POST /api/consent/check` - Check consent status
- `POST /api/consent/grant` - Grant consent
- `POST /api/consent/revoke` - Revoke consent
- `GET /api/consent/history/{phone_number}` - Get consent history

#### Data Management
- `GET /api/conversations/{phone_number}` - Get conversation history
- `POST /api/conversations/` - Save conversation
- `POST /api/conversations/pan` - Save PAN number
- `POST /api/conversations/tan` - Save TAN number

## 🔧 Configuration

### Environment Variables
- `DATABASE_URL`: PostgreSQL connection string
- `RASA_REST_URL`: Rasa server URL (default: http://127.0.0.1:5005/webhooks/rest/webhook)

### Rasa Configuration
- Modify `rasa_bot/config.yml` for NLU pipeline settings
- Update `rasa_bot/domain.yml` for intents and responses
- Add training data in `rasa_bot/data/` directory

## 📊 Database Schema

### Core Tables
- **phone_numbers**: User phone numbers with PAN/TAN references
- **conversations**: Chat message history
- **consents**: GDPR consent management
- **otp_verifications**: OTP verification records (disabled)
- **session_chathistory**: Session-based chat history
- **number_chathistory**: Phone number-based chat history

## 🔒 Security Features

- **Consent Management**: GDPR-compliant data processing consent
- **Session Tokens**: Limited concurrent session management
- **Input Validation**: Comprehensive input sanitization
- **SQL Injection Protection**: SQLAlchemy ORM protection

## 🌐 Multilingual Support

The bot supports both English and Hindi languages with:
- Comprehensive intent recognition in both languages
- Localized responses and menus
- Cultural context awareness for Indian tax systems

## 📈 Performance Features

- **Async Operations**: FastAPI async support for high concurrency
- **Database Connection Pooling**: Efficient database resource management
- **Session Token Management**: Prevents system overload
- **Caching**: Rasa model caching for faster responses

## 🧪 Testing

### OTP Flow Testing
Use the `test_otp_flow.html` file to test OTP functionality:
```bash
# Open test_otp_flow.html in browser
# Tests complete OTP generation and verification flow
```

### API Testing
Access Swagger UI at `http://localhost:8000/docs` for interactive API testing.

## 🐛 Troubleshooting

### Common Issues

1. **Rasa Server Not Starting**
   - Ensure all Rasa dependencies are installed
   - Check if port 5005 is available
   - Verify Rasa model is trained

2. **Database Connection Issues**
   - Verify PostgreSQL is running
   - Check database credentials in config
   - Ensure database exists

3. **Frontend Not Loading**
   - Check if FastAPI server is running on port 8000
   - Verify file paths in HTML

4. **Chat Not Responding**
   - Ensure all 4 terminals are running
   - Check Rasa server health at `/health` endpoint
   - Verify session token availability

## 📝 Development

### Adding New Intents
1. Add intent examples in `rasa_bot/data/nlu.yml`
2. Define responses in `rasa_bot/domain.yml`
3. Add stories in `rasa_bot/data/stories.yml`
4. Retrain Rasa model

### Extending API
1. Add new routes in `backend/routes/`
2. Create corresponding models in `backend/models/`
3. Implement services in `backend/services/`
4. Update schemas in `backend/schemas/`

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📞 Support

For support and queries:
- **Income Tax Helpline**: 1961
- **PAN/TAN Helpline**: 020-27218080
- **Email**: utiitsl.gsd@utiitsl.com

## 🔄 Version History

- **v1.0.0**: Initial release with basic PAN/TAN assistance
- **v1.1.0**: Added Hindi language support
- **v1.2.0**: Implemented consent management system
- **v1.3.0**: Added session management and OTP verification
- **v1.4.0**: Enhanced UI and improved conversation flow

---

**Note**: This chatbot is designed for informational purposes only. For official PAN/TAN applications and queries, please visit the official government websites or contact authorized service providers.