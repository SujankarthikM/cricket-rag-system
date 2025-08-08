import React from 'react';
import {
  Box,
  Avatar,
  Typography,
  Card,
  CardContent,
  Chip,
  Button,
  Link,
  Divider,
} from '@mui/material';
import {
  Person as UserIcon,
  SmartToy as BotIcon,
  OpenInNew as ExternalLinkIcon,
  Star as StarIcon,
} from '@mui/icons-material';

interface MatchResult {
  url: string;
  series_name: string;
  season?: string;
  score: number;
  teams: string[];
  match_number: string;
}

interface Message {
  id: string;
  text: string;
  isBot: boolean;
  timestamp: Date;
  matches?: MatchResult[];
}

interface ChatMessageProps {
  message: Message;
}

const ChatMessage: React.FC<ChatMessageProps> = ({ message }) => {
  const { text, isBot, timestamp, matches } = message;

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const getScoreColor = (score: number) => {
    if (score >= 0.8) return 'success';
    if (score >= 0.6) return 'warning';
    return 'default';
  };

  const handleMatchClick = (url: string) => {
    window.open(url, '_blank', 'noopener,noreferrer');
  };

  return (
    <Box
      sx={{
        display: 'flex',
        justifyContent: isBot ? 'flex-start' : 'flex-end',
        width: '100%',
        mb: 1,
      }}
    >
      <Box
        sx={{
          display: 'flex',
          flexDirection: isBot ? 'row' : 'row-reverse',
          alignItems: 'flex-start',
          maxWidth: '85%',
          gap: 1,
        }}
      >
        <Avatar
          sx={{
            bgcolor: isBot ? 'primary.main' : 'secondary.main',
            width: 32,
            height: 32,
            mt: 0.5,
          }}
        >
          {isBot ? <BotIcon fontSize="small" /> : <UserIcon fontSize="small" />}
        </Avatar>

        <Box sx={{ maxWidth: '100%' }}>
          <Card
            elevation={1}
            sx={{
              backgroundColor: isBot ? 'grey.50' : 'primary.main',
              color: isBot ? 'text.primary' : 'white',
              borderRadius: 2,
              '& .MuiCardContent-root:last-child': { pb: 2 },
            }}
          >
            <CardContent sx={{ p: 2 }}>
              <Typography
                variant="body1"
                sx={{
                  whiteSpace: 'pre-wrap',
                  wordBreak: 'break-word',
                  lineHeight: 1.5,
                }}
              >
                {text}
              </Typography>

              {/* Match Results */}
              {matches && matches.length > 0 && (
                <Box sx={{ mt: 2 }}>
                  {matches.map((match, index) => (
                    <Card
                      key={index}
                      variant="outlined"
                      sx={{
                        mb: index < matches.length - 1 ? 1 : 0,
                        cursor: 'pointer',
                        transition: 'all 0.2s',
                        '&:hover': {
                          boxShadow: 2,
                          transform: 'translateY(-2px)',
                        },
                      }}
                      onClick={() => handleMatchClick(match.url)}
                    >
                      <CardContent sx={{ p: 2 }}>
                        <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={1}>
                          <Typography variant="h6" color="text.primary" sx={{ fontSize: '1rem' }}>
                            Match #{index + 1}
                          </Typography>
                          <Box display="flex" alignItems="center" gap={1}>
                            <Chip
                              icon={<StarIcon />}
                              label={`${Math.round(match.score * 100)}%`}
                              size="small"
                              color={getScoreColor(match.score)}
                              variant="filled"
                            />
                            <ExternalLinkIcon fontSize="small" color="action" />
                          </Box>
                        </Box>

                        {match.teams.length > 0 && (
                          <Typography variant="body2" color="text.secondary" gutterBottom>
                            <strong>Teams:</strong> {match.teams.join(' vs ')}
                          </Typography>
                        )}

                        <Typography variant="body2" color="text.secondary" gutterBottom>
                          <strong>Series:</strong> {match.series_name}
                        </Typography>

                        {match.season && (
                          <Typography variant="body2" color="text.secondary" gutterBottom>
                            <strong>Season:</strong> {match.season}
                          </Typography>
                        )}

                        {match.match_number && (
                          <Typography variant="body2" color="text.secondary" gutterBottom>
                            <strong>Match:</strong> {match.match_number}
                          </Typography>
                        )}

                        <Divider sx={{ my: 1 }} />

                        <Link
                          href={match.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          sx={{
                            fontSize: '0.75rem',
                            wordBreak: 'break-all',
                            color: 'primary.main',
                            textDecoration: 'none',
                            '&:hover': { textDecoration: 'underline' },
                          }}
                        >
                          {match.url}
                        </Link>
                      </CardContent>
                    </Card>
                  ))}
                </Box>
              )}
            </CardContent>
          </Card>

          <Typography
            variant="caption"
            color="text.secondary"
            sx={{
              display: 'block',
              textAlign: isBot ? 'left' : 'right',
              mt: 0.5,
              ml: isBot ? 1 : 0,
              mr: isBot ? 0 : 1,
            }}
          >
            {formatTime(timestamp)}
          </Typography>
        </Box>
      </Box>
    </Box>
  );
};

export default ChatMessage;