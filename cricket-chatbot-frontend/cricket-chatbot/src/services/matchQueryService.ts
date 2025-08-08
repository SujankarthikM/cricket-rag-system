interface MatchResult {
  url: string;
  series_name: string;
  season?: string;
  score: number;
  teams: string[];
  match_number: string;
}

class MatchQueryService {
  private baseUrl = 'http://localhost:8000'; // We'll create a FastAPI backend

  async searchMatches(query: string): Promise<MatchResult[]> {
    try {
      const response = await fetch(`${this.baseUrl}/search`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data.matches || [];
    } catch (error) {
      console.error('Error searching matches:', error);
      // Fallback to mock data for demo purposes
      return this.getMockMatches(query);
    }
  }

  private getMockMatches(query: string): MatchResult[] {
    // Mock data for demonstration
    const mockMatches: MatchResult[] = [
      {
        url: "https://www.espncricinfo.com/series/the-ashes-2023-1336037/england-vs-australia-5th-test-1336047/match-report",
        series_name: "The Ashes (Australia in England), 2023",
        season: "2023",
        score: 0.95,
        teams: ["England", "Australia"],
        match_number: "5th"
      },
      {
        url: "https://www.espncricinfo.com/series/the-ashes-2023-1336037/england-vs-australia-4th-test-1336046/match-report",
        series_name: "The Ashes (Australia in England), 2023",
        season: "2023",
        score: 0.85,
        teams: ["England", "Australia"],
        match_number: "4th"
      },
      {
        url: "https://www.espncricinfo.com/series/the-ashes-2023-1336037/england-vs-australia-3rd-test-1336045/match-report",
        series_name: "The Ashes (Australia in England), 2023",
        season: "2023",
        score: 0.75,
        teams: ["England", "Australia"],
        match_number: "3rd"
      }
    ];

    // Simple filtering based on query keywords
    const queryLower = query.toLowerCase();
    if (queryLower.includes('ashes') && queryLower.includes('2023')) {
      return mockMatches;
    }

    if (queryLower.includes('india') && queryLower.includes('australia')) {
      return [
        {
          url: "https://www.espncricinfo.com/series/india-tour-of-australia-1999-00-62297/australia-vs-india-2nd-test-63866/match-report",
          series_name: "Border-Gavaskar Trophy (India in Australia), 1999/00",
          season: "1999/00",
          score: 0.88,
          teams: ["Australia", "India"],
          match_number: "2nd"
        }
      ];
    }

    if (queryLower.includes('ipl') && queryLower.includes('final')) {
      return [
        {
          url: "https://www.espncricinfo.com/series/indian-premier-league-2023-1345038/chennai-super-kings-vs-gujarat-titans-final-1359476/match-report",
          series_name: "Indian Premier League 2023",
          season: "2023",
          score: 0.92,
          teams: ["Chennai Super Kings", "Gujarat Titans"],
          match_number: "final"
        }
      ];
    }

    // Return empty array if no matches
    return [];
  }
}

export const matchQueryService = new MatchQueryService();