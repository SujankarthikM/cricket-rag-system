# Cricket Chatbot - Simplified Architecture for Presentation

## 1. High-Level System Overview

```mermaid
graph TD
    User[User Query] --> Router[MCP Intelligent Router]
    
    Router --> Live[Live Data Tools]
    Router --> Historical[RAG System]
    Router --> BallDB[Ball Database Tool]
    Router --> Analysis[Player Analysis Tools]
    Router --> Viz[Visualization Tools]
    
    Live --> API1[Cricket APIs]
    Live --> Weather[Weather APIs]
    
    Historical --> VectorDB[(Vector Database)]
    
    BallDB --> MySQL[(MySQL Ball Database)]
    Analysis --> PlayerDB[(Player Database)]
    Viz --> Charts[Chart Generation]
    
    API1 --> Response[Response Generator]
    Weather --> Response
    VectorDB --> Response
    MySQL --> Response
    PlayerDB --> Response
    Charts --> Response
    
    Response --> User
    
    classDef user fill:#e1f5fe
    classDef router fill:#f3e5f5
    classDef tools fill:#e8f5e8
    classDef data fill:#fff3e0
    classDef response fill:#fce4ec
    
    class User user
    class Router router
    class Live,Historical,BallDB,Analysis,Viz tools
    class API1,Weather,VectorDB,MySQL,PlayerDB,Charts data
    class Response response
```

## 2. MCP Tool Decision Logic

```mermaid
flowchart TD
    Query[User Query] --> Classify[Query Classification]
    
    Classify --> Live{Live Data Needed?}
    Classify --> Historical{Historical Analysis?}
    Classify --> Advanced{Advanced Analysis?}
    
    Live -->|Yes| LiveTools[Live Score + Commentary]
    Historical -->|Yes| RAG[RAG Database Search]
    Advanced -->|Yes| SpecialTools[Ball DB + Social Sentiment]
    
    LiveTools --> Combine[Response Generation]
    RAG --> Combine
    SpecialTools --> Combine
    
    Combine --> Output[Final Response]
    
    classDef query fill:#ffebee
    classDef decision fill:#e8f5e8
    classDef tools fill:#e3f2fd
    classDef output fill:#f1f8e9
    
    class Query,Output query
    class Classify,Live,Historical,Advanced decision
    class LiveTools,RAG,SpecialTools,Combine tools
```

## 3. Data Sources and Flow

```mermaid
graph LR
    subgraph "Live Data"
        ESPN[ESPNCricinfo]
        Cricbuzz[Cricbuzz]
        Weather[Weather APIs]
    end
    
    subgraph "Historical Data"
        Archives[Cricket Archives]
        Stats[Player Statistics]
        Commentary[Match Commentary]
    end
    
    subgraph "Advanced Sources"
        BallDB[Ball-by-Ball Database]
        SocialMedia[Social Media]
    end
    
    ESPN --> Cache[(Redis Cache)]
    Cricbuzz --> Cache
    Weather --> Cache
    
    Archives --> Vector[(Vector Database)]
    Stats --> Vector
    Commentary --> Vector
    
    BallDB --> AIQuery[AI Query Engine]
    SocialMedia --> Sentiment[Sentiment Analysis]
    
    Cache --> Response[Response System]
    Vector --> Response
    AIQuery --> Response
    Sentiment --> Response
    
    classDef live fill:#ffebee
    classDef historical fill:#e8f5e8
    classDef advanced fill:#e3f2fd
    classDef processing fill:#f1f8e9
    
    class ESPN,Cricbuzz,Weather live
    class Archives,Stats,Commentary historical
    class BallDB,SocialMedia advanced
    class Cache,Vector,AIQuery,Sentiment,Response processing
```

## 4. Core MCP Tools

```mermaid
graph TD
    subgraph "9 MCP Tools"
        T1[Live Scores]
        T2[Commentary Scraper]
        T3[Weather Data]
        T4[Historical Stats RAG]
        T5[Match Predictions]
        T6[Ball Database AI]
        T7[Player Comparison]
        T8[Social Sentiment]
        T9[Data Visualization]
    end
    
    subgraph "Tool Categories"
        Real[Real-time Tools]
        Historical[Historical Tools]
        Advanced[Advanced Analytics]
    end
    
    T1 --> Real
    T2 --> Real
    T3 --> Real
    
    T4 --> Historical
    T5 --> Historical
    
    T6 --> Advanced
    T7 --> Advanced
    T8 --> Advanced
    T9 --> Advanced
    
    Real --> Output[User Response]
    Historical --> Output
    Advanced --> Output
    
    classDef tools fill:#e3f2fd
    classDef categories fill:#e8f5e8
    classDef output fill:#ffebee
    
    class T1,T2,T3,T4,T5,T6,T7,T8,T9 tools
    class Real,Historical,Advanced categories
    class Output output
```

## 5. System Architecture Components

```mermaid
graph TB
    subgraph "Frontend"
        UI[Web Interface]
        API[REST API]
    end
    
    subgraph "Core System"
        Router[MCP Router]
        Tools[9 MCP Tools]
        LLM[Language Model]
    end
    
    subgraph "Data Layer"
        Live[(Live Data)]
        Vector[(Vector DB)]
        MySQL[(Ball Database)]
    end
    
    UI --> Router
    API --> Router
    
    Router --> Tools
    Tools --> LLM
    
    Tools --> Live
    Tools --> Vector
    Tools --> MySQL
    
    LLM --> UI
    LLM --> API
    
    classDef frontend fill:#e1f5fe
    classDef core fill:#e8f5e8
    classDef data fill:#fff3e0
    
    class UI,API frontend
    class Router,Tools,LLM core
    class Live,Vector,MySQL data
```

## 6. Query Processing Flow

```mermaid
flowchart LR
    Input[User Query] --> Process[Query Processing]
    Process --> Route[MCP Routing]
    Route --> Execute[Tool Execution]
    Execute --> Generate[Response Generation]
    Generate --> Output[User Response]
    
    classDef flow fill:#e3f2fd
    class Input,Process,Route,Execute,Generate,Output flow
```

These simplified diagrams focus on the key concepts and flow without overwhelming detail, perfect for a professor presentation!