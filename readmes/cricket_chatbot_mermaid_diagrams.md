

```mermaid
graph TB
    subgraph "User Interface Layer"
        UI[User Interface]
        Voice[Voice Input]
        Text[Text Input]
        Image[Image Input]
    end
    
    subgraph "Query Processing Engine"
        QP[Query Processor]
        IC[Intent Classifier]
        NER[Entity Recognition]
        TC[Temporal Context]
        QC[Query Complexity Analyzer]
    end
    
    subgraph "MCP Intelligent Router"
        Router[MCP Router]
        DM[Decision Matrix]
        TM[Tool Mapper]
    end
    
    subgraph "MCP Tools Layer"
        subgraph "Core Tools"
            LST[Live Score Tool]
            HST[Historical Stats Tool] 
            CST[Commentary Scraper Tool]
            WT[Weather Tool]
            PT[Prediction Tool]
        end
        
        subgraph "Advanced Tools"
            BDT[Ball Database Tool]
            PCT[Player Comparison Tool]
            SST[Social Sentiment Tool]
            VT[Visualization Tool]
        end
    end
    
    subgraph "Data Sources & Processing"
        subgraph "Live Data Sources"
            ESPN[ESPNCricinfo API]
            CB[Cricbuzz API]
            Weather[Weather APIs]
            Social[Social Media APIs]
        end
        
        subgraph "Historical Data Sources"
            MySQL[(MySQL Ball Database)]
            VectorDB[(Vector Database - RAG)]
            PlayerDB[(Player Database)]
            MatchDB[(Match Database)]
        end
        
        subgraph "ML & AI Models"
            LLM[Large Language Model]
            MLModels[ML Prediction Models]
            SentimentAI[Sentiment Analysis AI]
            ChartAI[Chart Recommendation AI]
        end
    end
    
    subgraph "Response Generation"
        RG[Response Generator]
        VA[Response Validator]
        VIZ[Visualization Generator]
        Formatter[Response Formatter]
    end
    
    subgraph "Caching & Optimization"
        Redis[(Redis Cache)]
        CDN[Content Delivery Network]
        LoadBalancer[Load Balancer]
    end
    
    %% User Flow
    UI --> QP
    Voice --> QP
    Text --> QP
    Image --> QP
    
    %% Query Processing Flow
    QP --> IC
    QP --> NER
    QP --> TC
    QP --> QC
    
    %% Routing Flow
    IC --> Router
    NER --> Router
    TC --> Router
    QC --> Router
    
    Router --> DM
    DM --> TM
    
    %% Tool Selection
    TM --> LST
    TM --> HST
    TM --> CST
    TM --> WT
    TM --> PT
    TM --> BDT
    TM --> PCT
    TM --> SST
    TM --> VT
    
    %% Data Source Connections
    LST --> ESPN
    LST --> CB
    CST --> ESPN
    CST --> CB
    WT --> Weather
    SST --> Social
    
    HST --> VectorDB
    BDT --> MySQL
    PCT --> PlayerDB
    PCT --> MatchDB
    
    %% AI/ML Connections
    BDT --> LLM
    PCT --> MLModels
    SST --> SentimentAI
    VT --> ChartAI
    PT --> MLModels
    
    %% Response Generation
    LST --> RG
    HST --> RG
    CST --> RG
    WT --> RG
    PT --> RG
    BDT --> RG
    PCT --> RG
    SST --> RG
    VT --> VIZ
    
    RG --> VA
    VA --> Formatter
    VIZ --> Formatter
    
    %% Caching
    Router --> Redis
    ESPN --> Redis
    CB --> Redis
    Weather --> Redis
    Social --> Redis
    
    %% Load Balancing
    LoadBalancer --> QP
    CDN --> UI
    
    %% Final Output
    Formatter --> UI
    
    %% Styling
    classDef userLayer fill:#e1f5fe
    classDef processingLayer fill:#f3e5f5
    classDef toolsLayer fill:#e8f5e8
    classDef dataLayer fill:#fff3e0
    classDef aiLayer fill:#fce4ec
    classDef cacheLayer fill:#f1f8e9
    
    class UI,Voice,Text,Image userLayer
    class QP,IC,NER,TC,QC,Router,DM,TM processingLayer
    class LST,HST,CST,WT,PT,BDT,PCT,SST,VT toolsLayer
    class ESPN,CB,Weather,Social,MySQL,VectorDB,PlayerDB,MatchDB dataLayer
    class LLM,MLModels,SentimentAI,ChartAI aiLayer
    class Redis,CDN,LoadBalancer cacheLayer
```



```mermaid
flowchart TD
    Start([User Query]) --> Analyze[Analyze Query]
    
    Analyze --> Intent{Classify Intent}
    Analyze --> Entities{Extract Entities}
    Analyze --> Temporal{Temporal Context}
    
    Intent --> Live{Live Data?}
    Intent --> Historical{Historical Data?}
    Intent --> Comparison{Comparison Query?}
    Intent --> Sentiment{Sentiment Query?}
    Intent --> Visualization{Viz Request?}
    Intent --> BallLevel{Ball-level Data?}
    
    %% Live Data Path
    Live -->|Yes| LiveType{Type?}
    LiveType --> Scores[Live Scores] --> LST[Live Score Tool]
    LiveType --> Commentary[Commentary] --> CST[Commentary Scraper]
    LiveType --> Weather[Weather] --> WT[Weather Tool]
    
    %% Historical Data Path
    Historical -->|Yes| HistType{Data Type?}
    HistType --> Stats[General Stats] --> HST[Historical Stats Tool]
    HistType --> Career[Career Data] --> RAG[RAG Database]
    
    %% Ball-level Analysis
    BallLevel -->|Yes| BallQuery{Query Type?}
    BallQuery --> Specific[Specific Deliveries] --> BDT[Ball Database Tool]
    BallQuery --> Patterns[Bowling Patterns] --> BDT
    BallQuery --> Analysis[Delivery Analysis] --> BDT
    
    %% Player Comparison
    Comparison -->|Yes| CompType{Comparison Type?}
    CompType --> Players[Player vs Player] --> PCT[Player Comparison Tool]
    CompType --> Teams[Team Comparison] --> PCT
    CompType --> Performance[Performance Analysis] --> PCT
    
    %% Sentiment Analysis
    Sentiment -->|Yes| SentType{Sentiment Type?}
    SentType --> PlayerSent[Player Sentiment] --> SST[Social Sentiment Tool]
    SentType --> TeamSent[Team Sentiment] --> SST
    SentType --> MatchSent[Match Sentiment] --> SST
    
    %% Visualization
    Visualization -->|Yes| VizType{Chart Type?}
    VizType --> Trends[Trend Charts] --> VT[Visualization Tool]
    VizType --> Heatmaps[Heatmaps] --> VT
    VizType --> Comparisons[Comparison Charts] --> VT
    
    %% Prediction Path
    Intent --> Prediction{Prediction?}
    Prediction -->|Yes| PredType{Prediction Type?}
    PredType --> MatchPred[Match Outcome] --> PT[Prediction Tool]
    PredType --> PlayerPred[Player Performance] --> PT
    PredType --> TournamentPred[Tournament] --> PT
    
    %% Multi-tool scenarios
    BDT --> Combine{Combine with other tools?}
    PCT --> Combine
    SST --> Combine
    VT --> Combine
    LST --> Combine
    HST --> Combine
    CST --> Combine
    WT --> Combine
    PT --> Combine
    
    Combine -->|Yes| MultiTool[Multi-tool Response]
    Combine -->|No| SingleResponse[Single Tool Response]
    
    MultiTool --> Response[Generate Response]
    SingleResponse --> Response
    
    Response --> End([Deliver to User])
    
    %% Styling
    classDef startEnd fill:#ffcdd2
    classDef decision fill:#e1bee7
    classDef tool fill:#c8e6c9
    classDef process fill:#bbdefb
    
    class Start,End startEnd
    class Intent,Entities,Temporal,Live,Historical,Comparison,Sentiment,Visualization,BallLevel,LiveType,HistType,BallQuery,CompType,SentType,VizType,Prediction,PredType,Combine decision
    class LST,CST,WT,HST,BDT,PCT,SST,VT,PT tool
    class Analyze,MultiTool,SingleResponse,Response process
```

## 3. Data Flow Architecture

```mermaid
graph LR
    subgraph "Real-time Data Pipeline"
        RT1[Live Scores API] -->|30s| Cache1[(Redis Cache)]
        RT2[Commentary Feed] -->|10s| Cache2[(Redis Cache)]
        RT3[Weather API] -->|10min| Cache3[(Redis Cache)]
        RT4[Social Media APIs] -->|5min| Cache4[(Redis Cache)]
        
        Cache1 --> Processor1[Live Data Processor]
        Cache2 --> Processor2[Commentary Processor]
        Cache3 --> Processor3[Weather Processor]
        Cache4 --> Processor4[Sentiment Processor]
    end
    
    subgraph "Historical Data Pipeline"
        Scraper1[ESPN Historical Scraper] --> ETL1[ETL Process]
        Scraper2[Cricbuzz Archive Scraper] --> ETL2[ETL Process]
        Scraper3[ICC Official Data] --> ETL3[ETL Process]
        
        ETL1 --> Vectorizer[Text Vectorization]
        ETL2 --> Vectorizer
        ETL3 --> Vectorizer
        
        ETL1 --> Structured[(Structured Database)]
        ETL2 --> Structured
        ETL3 --> Structured
        
        Vectorizer --> VectorStore[(Vector Database)]
    end
    
    subgraph "Ball-by-Ball Pipeline"
        BallScraper[Ball-by-Ball Scraper] --> BallETL[Ball Data ETL]
        BallETL --> BallDB[(MySQL Ball Database)]
        BallDB --> AIQuery[AI Query Generator]
        AIQuery --> SQLProcessor[SQL Processor]
    end
    
    subgraph "ML Pipeline"
        FeatureEng[Feature Engineering] --> MLTraining[ML Model Training]
        MLTraining --> ModelStore[(Model Storage)]
        ModelStore --> Inference[Inference Engine]
        
        Structured --> FeatureEng
        BallDB --> FeatureEng
        VectorStore --> FeatureEng
    end
    
    subgraph "Response Generation Pipeline"
        Processor1 --> ResponseEngine[Response Engine]
        Processor2 --> ResponseEngine
        Processor3 --> ResponseEngine
        Processor4 --> ResponseEngine
        
        VectorStore --> RAGEngine[RAG Engine]
        RAGEngine --> ResponseEngine
        
        SQLProcessor --> ResponseEngine
        Inference --> ResponseEngine
        
        ResponseEngine --> LLM[Large Language Model]
        LLM --> ResponseValidator[Response Validator]
        ResponseValidator --> Formatter[Response Formatter]
    end
    
    subgraph "Visualization Pipeline"
        ResponseEngine --> ChartAI[Chart Recommendation AI]
        ChartAI --> VizEngine[Visualization Engine]
        VizEngine --> ChartRenderer[Chart Renderer]
        ChartRenderer --> InteractiveCharts[Interactive Charts]
    end
    
    Formatter --> UserInterface[User Interface]
    InteractiveCharts --> UserInterface
    
    %% Update flows
    UserInterface -.->|Feedback| MLTraining
    ResponseValidator -.->|Quality Metrics| MLTraining
    
    %% Styling
    classDef realtime fill:#ffebee
    classDef historical fill:#e8f5e8
    classDef balldata fill:#e3f2fd
    classDef ml fill:#fce4ec
    classDef response fill:#fff3e0
    classDef viz fill:#f1f8e9
    
    class RT1,RT2,RT3,RT4,Cache1,Cache2,Cache3,Cache4,Processor1,Processor2,Processor3,Processor4 realtime
    class Scraper1,Scraper2,Scraper3,ETL1,ETL2,ETL3,Vectorizer,Structured,VectorStore,RAGEngine historical
    class BallScraper,BallETL,BallDB,AIQuery,SQLProcessor balldata
    class FeatureEng,MLTraining,ModelStore,Inference ml
    class ResponseEngine,LLM,ResponseValidator,Formatter,UserInterface response
    class ChartAI,VizEngine,ChartRenderer,InteractiveCharts viz
```


```mermaid
erDiagram
    PLAYERS {
        uuid player_id PK
        string name
        string country
        string role
        string batting_style
        string bowling_style
        date debut_date
        json career_stats
        timestamp created_at
        timestamp updated_at
    }
    
    TEAMS {
        uuid team_id PK
        string name
        string country
        string short_name
        json team_stats
        timestamp created_at
    }
    
    MATCHES {
        uuid match_id PK
        string match_type
        json teams
        string venue
        date match_date
        json result
        json scorecard
        text commentary
        timestamp created_at
    }
    
    BALLS {
        uuid ball_id PK
        uuid match_id FK
        int over_number
        int ball_number
        uuid batsman_id FK
        uuid bowler_id FK
        int runs_scored
        string wicket_type
        json field_positions
        string pitch_conditions
        string delivery_type
        timestamp ball_time
    }
    
    LIVE_MATCHES {
        uuid match_id PK
        json current_score
        json current_over
        string match_status
        json weather_conditions
        timestamp last_updated
    }
    
    VECTOR_EMBEDDINGS {
        uuid embedding_id PK
        string content_type
        uuid source_id
        vector embedding_vector
        json metadata
        timestamp created_at
    }
    
    PLAYER_STATS {
        uuid stat_id PK
        uuid player_id FK
        uuid match_id FK
        string format
        json batting_stats
        json bowling_stats
        json fielding_stats
        timestamp created_at
    }
    
    SOCIAL_SENTIMENT {
        uuid sentiment_id PK
        string entity_type
        uuid entity_id
        string platform
        float sentiment_score
        json sentiment_data
        timestamp analyzed_at
    }
    
    ML_PREDICTIONS {
        uuid prediction_id PK
        uuid match_id FK
        string prediction_type
        json prediction_data
        float confidence_score
        timestamp created_at
    }
    
    %% Relationships
    PLAYERS ||--o{ BALLS : "bowls/bats"
    MATCHES ||--o{ BALLS : "contains"
    MATCHES ||--o{ LIVE_MATCHES : "has_live_data"
    PLAYERS ||--o{ PLAYER_STATS : "has_stats"
    MATCHES ||--o{ PLAYER_STATS : "recorded_in"
    MATCHES ||--o{ ML_PREDICTIONS : "predicted_for"
    PLAYERS ||--o{ SOCIAL_SENTIMENT : "mentioned_in"
    TEAMS ||--o{ SOCIAL_SENTIMENT : "mentioned_in"
    MATCHES ||--o{ SOCIAL_SENTIMENT : "mentioned_in"
```


```mermaid
graph TD
    subgraph "Query Types"
        Q1[Live Match Query]
        Q2[Historical Stats Query]
        Q3[Player Comparison Query]
        Q4[Ball Analysis Query]
        Q5[Sentiment Query]
        Q6[Prediction Query]
        Q7[Visualization Query]
    end
    
    subgraph "Tool Combinations"
        T1[Single Tool Response]
        T2[Live + Weather]
        T3[Historical + Comparison]
        T4[Ball DB + Visualization]
        T5[Sentiment + Prediction]
        T6[Multi-source Analysis]
    end
    
    subgraph "Response Types"
        R1[Text Response]
        R2[Data Tables]
        R3[Interactive Charts]
        R4[Sentiment Dashboard]
        R5[Prediction Report]
        R6[Comparison Analysis]
    end
    
    %% Query to Tool mapping
    Q1 --> T1
    Q1 --> T2
    Q2 --> T1
    Q2 --> T3
    Q3 --> T3
    Q3 --> T6
    Q4 --> T1
    Q4 --> T4
    Q5 --> T1
    Q5 --> T5
    Q6 --> T5
    Q6 --> T6
    Q7 --> T4
    Q7 --> T6
    
    %% Tool to Response mapping
    T1 --> R1
    T1 --> R2
    T2 --> R1
    T2 --> R2
    T3 --> R6
    T3 --> R3
    T4 --> R3
    T4 --> R2
    T5 --> R4
    T5 --> R5
    T6 --> R3
    T6 --> R5
    T6 --> R6
    
    %% Examples
    Q1 -.->|Example: "Current score of IND vs AUS"| T2
    Q2 -.->|Example: "Kohli's career average"| T1
    Q3 -.->|Example: "Compare Bumrah vs Starc"| T3
    Q4 -.->|Example: "Yorkers in death overs"| T4
    Q5 -.->|Example: "Fan reaction to selection"| T1
    Q6 -.->|Example: "Who will win today?"| T5
    Q7 -.->|Example: "Show batting trends"| T4
    
    %% Styling
    classDef query fill:#e1f5fe
    classDef tool fill:#e8f5e8
    classDef response fill:#fff3e0
    
    class Q1,Q2,Q3,Q4,Q5,Q6,Q7 query
    class T1,T2,T3,T4,T5,T6 tool
    class R1,R2,R3,R4,R5,R6 response
```


```mermaid
graph TB
    subgraph "Client Layer"
        Web[Web Browser]
        Mobile[Mobile App]
        API[API Clients]
    end
    
    subgraph "CDN & Load Balancing"
        CDN[Content Delivery Network]
        LB[Load Balancer]
        SSL[SSL Termination]
    end
    
    subgraph "Application Layer"
        App1[App Server 1]
        App2[App Server 2]
        App3[App Server 3]
    end
    
    subgraph "Caching Layers"
        L1[L1 Cache - Application Memory]
        L2[L2 Cache - Redis Cluster]
        L3[L3 Cache - Database Query Cache]
    end
    
    subgraph "Data Processing"
        MCP[MCP Router]
        Tools[MCP Tools]
        AI[AI Processing]
    end
    
    subgraph "Data Storage"
        MySQL[(MySQL Ball DB)]
        Vector[(Vector DB)]
        Postgres[(PostgreSQL)]
        Files[File Storage]
    end
    
    %% Client connections
    Web --> CDN
    Mobile --> CDN
    API --> LB
    
    %% Load balancing
    CDN --> LB
    LB --> SSL
    SSL --> App1
    SSL --> App2
    SSL --> App3
    
    %% Application to cache
    App1 --> L1
    App2 --> L1
    App3 --> L1
    
    L1 -->|Cache Miss| L2
    L2 -->|Cache Miss| L3
    L3 -->|Cache Miss| MCP
    
    %% Cache hit paths
    L1 -.->|Cache Hit - 1ms| App1
    L2 -.->|Cache Hit - 5ms| L1
    L3 -.->|Cache Hit - 20ms| L2
    
    %% Processing flow
    MCP --> Tools
    Tools --> AI
    
    %% Data access
    MCP --> MySQL
    MCP --> Vector
    MCP --> Postgres
    Tools --> Files
    
    %% Cache population
    MySQL --> L3
    Vector --> L3
    Postgres --> L3
    
    %% Cache TTL Labels
    L1 -.->|TTL: 5min| CacheLabel1[Application Cache]
    L2 -.->|TTL: Variable| CacheLabel2[Redis Cache<br/>Live: 30s<br/>Historical: 1h<br/>Static: 24h]
    L3 -.->|TTL: 30min| CacheLabel3[Query Cache]
    
    %% Performance metrics
    subgraph "Performance Targets"
        P1[Response Time: <200ms]
        P2[Cache Hit Ratio: >80%]
        P3[Throughput: 1000 RPS]
        P4[Availability: 99.9%]
    end
    
    %% Styling
    classDef client fill:#e1f5fe
    classDef cdn fill:#f3e5f5
    classDef app fill:#e8f5e8
    classDef cache fill:#fff3e0
    classDef data fill:#fce4ec
    classDef perf fill:#f1f8e9
    
    class Web,Mobile,API client
    class CDN,LB,SSL cdn
    class App1,App2,App3 app
    class L1,L2,L3,CacheLabel1,CacheLabel2,CacheLabel3 cache
    class MySQL,Vector,Postgres,Files,MCP,Tools,AI data
    class P1,P2,P3,P4 perf
```

These comprehensive Mermaid diagrams show the complete architecture, data flows, tool interactions, database relationships, and performance optimization strategies for your cricket chatbot system.