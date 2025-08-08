# 🏏 Cricket Match Finder Chatbot

A professional React-based chatbot interface for querying cricket matches using natural language. Built with React TypeScript and Material-UI.

## Features

✅ **Natural Language Queries**: Ask questions like "Ashes 2023 last test" or "India vs Australia 1999 2nd test"
✅ **Professional UI**: Modern Material-UI design with responsive layout
✅ **Real-time Search**: Instant match results with confidence scores
✅ **Match Details**: Teams, series, seasons, and direct links to ESPN Cricinfo
✅ **Suggested Queries**: Quick access to popular cricket match queries
✅ **TypeScript**: Full type safety and better development experience

## Project Structure

```
cricket-chatbot-frontend/
├── cricket-chatbot/          # React TypeScript app
│   ├── src/
│   │   ├── components/
│   │   │   ├── CricketChatbot.tsx    # Main chatbot component
│   │   │   └── ChatMessage.tsx       # Message display component
│   │   ├── services/
│   │   │   └── matchQueryService.ts  # API service layer
│   │   └── App.tsx                   # Main app component
├── backend/
│   ├── main.py              # FastAPI backend server
│   └── requirements.txt     # Python dependencies
├── start_frontend.sh        # Frontend startup script
└── start_backend.sh         # Backend startup script
```

## Quick Start

### 1. Start the Backend (Terminal 1)

```bash
cd /Users/skarthikm/Documents/finalyear/cricket-chatbot-frontend
chmod +x start_backend.sh
./start_backend.sh
```

### 2. Start the Frontend (Terminal 2)

```bash
cd /Users/skarthikm/Documents/finalyear/cricket-chatbot-frontend
chmod +x start_frontend.sh
./start_frontend.sh
```

### 3. Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## Usage Examples

Try these queries in the chatbot:

- **"Ashes 2023 last test"** - Find the final Ashes match of 2023
- **"India vs Australia Border Gavaskar 2023"** - Search Border-Gavaskar Trophy matches
- **"IPL 2023 final"** - Find the IPL 2023 final match
- **"World Cup 1983 India vs Zimbabwe"** - Historical World Cup matches
- **"England vs India 5th test"** - Recent England vs India series

## Technical Details

### Frontend Stack
- **React 18** with TypeScript
- **Material-UI (MUI)** for professional UI components
- **Responsive Design** for mobile and desktop
- **Real-time Chat Interface** with smooth animations

### Backend Stack
- **FastAPI** for high-performance API
- **Python Match Query System** with fuzzy matching
- **CORS enabled** for cross-origin requests
- **Pydantic** for data validation

### Data Sources
- **Test Matches**: 937 matches
- **ODI Matches**: 1,372 matches  
- **T20I Matches**: 824 matches
- **IPL Matches**: 1,177 matches

## Development

### Frontend Development
```bash
cd cricket-chatbot
npm start          # Start development server
npm run build      # Build for production
npm test           # Run tests
```

### Backend Development
```bash
cd backend
uvicorn main:app --reload  # Start with auto-reload
```

## API Endpoints

- **POST /search** - Search for cricket matches
- **GET /health** - Health check and match counts
- **GET /** - API status

## Dependencies

### Frontend
- React, TypeScript, Material-UI
- Axios for API calls
- React Markdown for message formatting

### Backend
- FastAPI, Uvicorn, Pydantic
- Pandas, FuzzyWuzzy for match processing
- CORS middleware for cross-origin support

---

Built with ❤️ for cricket fans worldwide! 🏏