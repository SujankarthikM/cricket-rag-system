import React, { useState, useRef, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  TextField,
  IconButton,
  List,
  ListItem,
  Avatar,
  Chip,
  Fade,
  Container,
  Card,
  CardContent,
} from '@mui/material';
import {
  Send as SendIcon,
  SportsBaseball as CricketIcon,
  Person as UserIcon,
  SmartToy as BotIcon,
} from '@mui/icons-material';
import ChatMessage from './ChatMessage';
import { matchQueryService } from '../services/matchQueryService';

interface Message {
  id: string;
  text: string;
  isBot: boolean;
  timestamp: Date;
  matches?: MatchResult[];
}

interface MatchResult {
  url: string;
  series_name: string;
  season?: string;
  score: number;
  teams: string[];
  match_number: string;
}

const CricketChatbot: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      text: '🏏 Welcome to Cricket Match Finder! I can help you find specific cricket matches. Try queries like:\n\n• "India vs Australia 1999 2nd test"\n• "Ashes 2023 5th test"\n• "IPL 2007 final"\n• "World Cup 1983 India vs Zimbabwe"',
      isBot: true,
      timestamp: new Date(),
    },
  ]);
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async () => {
    if (!inputText.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      text: inputText,
      isBot: false,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputText('');
    setIsLoading(true);

    try {
      const matches = await matchQueryService.searchMatches(inputText);
      
      let botResponse = '';
      if (matches.length === 0) {
        botResponse = "❌ No matches found for your query. Try being more specific with team names, years, or series names.";
      } else {
        botResponse = `✅ Found ${matches.length} match${matches.length > 1 ? 'es' : ''} for "${inputText}":`;
      }

      const botMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: botResponse,
        isBot: true,
        timestamp: new Date(),
        matches: matches.length > 0 ? matches : undefined,
      };

      setMessages(prev => [...prev, botMessage]);
    } catch (error) {
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: '❌ Sorry, there was an error processing your request. Please try again.',
        isBot: true,
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      handleSendMessage();
    }
  };

  const suggestedQueries = [
    "Ashes 2023 last test",
    "India vs Australia Border Gavaskar 2023",
    "IPL 2023 final",
    "World Cup 2023 final",
  ];

  const handleSuggestionClick = (query: string) => {
    setInputText(query);
  };

  return (
    <Container maxWidth="md" sx={{ height: '100vh', display: 'flex', flexDirection: 'column', py: 2 }}>
      {/* Header */}
      <Paper
        elevation={3}
        sx={{
          p: 3,
          mb: 2,
          background: 'linear-gradient(45deg, #1976d2 30%, #388e3c 90%)',
          color: 'white',
          borderRadius: 3,
        }}
      >
        <Box display="flex" alignItems="center" gap={2}>
          <Avatar sx={{ bgcolor: 'rgba(255,255,255,0.2)', width: 56, height: 56 }}>
            <CricketIcon fontSize="large" />
          </Avatar>
          <Box>
            <Typography variant="h4" component="h1" fontWeight="bold">
              Cricket Match Finder
            </Typography>
            <Typography variant="subtitle1" sx={{ opacity: 0.9 }}>
              Your AI assistant for cricket match queries
            </Typography>
          </Box>
        </Box>
      </Paper>

      {/* Suggested Queries */}
      {messages.length === 1 && (
        <Fade in={true}>
          <Paper elevation={1} sx={{ p: 2, mb: 2, borderRadius: 2 }}>
            <Typography variant="subtitle2" color="text.secondary" gutterBottom>
              Try these popular queries:
            </Typography>
            <Box display="flex" flexWrap="wrap" gap={1}>
              {suggestedQueries.map((query, index) => (
                <Chip
                  key={index}
                  label={query}
                  onClick={() => handleSuggestionClick(query)}
                  variant="outlined"
                  clickable
                  size="small"
                  sx={{ '&:hover': { backgroundColor: 'primary.light', color: 'white' } }}
                />
              ))}
            </Box>
          </Paper>
        </Fade>
      )}

      {/* Chat Messages */}
      <Paper
        elevation={2}
        sx={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
          borderRadius: 3,
        }}
      >
        <Box
          sx={{
            flex: 1,
            overflow: 'auto',
            p: 1,
            background: 'linear-gradient(to bottom, #f8f9fa, #ffffff)',
          }}
        >
          <List sx={{ py: 0 }}>
            {messages.map((message) => (
              <ListItem key={message.id} sx={{ py: 1, px: 2 }}>
                <ChatMessage message={message} />
              </ListItem>
            ))}
            {isLoading && (
              <ListItem sx={{ py: 1, px: 2 }}>
                <Box display="flex" alignItems="center" gap={2}>
                  <Avatar sx={{ bgcolor: 'primary.main', width: 32, height: 32 }}>
                    <BotIcon fontSize="small" />
                  </Avatar>
                  <Typography variant="body2" color="text.secondary">
                    Searching for matches...
                  </Typography>
                </Box>
              </ListItem>
            )}
            <div ref={messagesEndRef} />
          </List>
        </Box>

        {/* Input Area */}
        <Box
          sx={{
            p: 2,
            borderTop: '1px solid',
            borderColor: 'divider',
            backgroundColor: 'background.paper',
          }}
        >
          <Box display="flex" gap={1} alignItems="flex-end">
            <TextField
              fullWidth
              multiline
              maxRows={3}
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask me about any cricket match... (e.g., 'India vs Australia 2023 1st test')"
              variant="outlined"
              disabled={isLoading}
              sx={{
                '& .MuiOutlinedInput-root': {
                  borderRadius: 3,
                },
              }}
            />
            <IconButton
              color="primary"
              onClick={handleSendMessage}
              disabled={!inputText.trim() || isLoading}
              sx={{
                bgcolor: 'primary.main',
                color: 'white',
                '&:hover': { bgcolor: 'primary.dark' },
                '&:disabled': { bgcolor: 'grey.300' },
                width: 48,
                height: 48,
              }}
            >
              <SendIcon />
            </IconButton>
          </Box>
        </Box>
      </Paper>
    </Container>
  );
};

export default CricketChatbot;