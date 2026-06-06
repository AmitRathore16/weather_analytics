const express = require("express");
const cors = require("cors");
const mysql = require("mysql2/promise");
const Groq = require("groq-sdk");
const { spawn } = require("child_process");
const path = require("path");
require("dotenv").config({ path: path.join(__dirname, "../.env") });

const app = express();
app.use(cors());
app.use(express.json());

const PORT = process.env.PORT || 5001;

const TRACKED_CITIES = [
  "ajmer", "bangalore", "bhopal", "chennai", "hyderabad",
  "jaipur", "kochi", "kolkata", "lucknow", "mumbai",
  "new delhi", "pune", "surat", "kota",
];

// Initialize Gemini API
const ai = new Groq({
  apiKey: process.env.GROQ_API_KEY
});
// Database Pool Connection
let pool;
try {
  pool = mysql.createPool({
    host: process.env.DB_HOST || "localhost",
    user: process.env.DB_USER || "root",
    password: process.env.DB_PASSWORD,
    database: process.env.DB_NAME || "weather_report",
    port: parseInt(process.env.DB_PORT || "3306"),
    waitForConnections: true,
    connectionLimit: 10,
    queueLimit: 0
  });
  console.log("MySQL Database Connection Pool initialized.");
} catch (err) {
  console.error("Failed to initialize MySQL Connection Pool:", err);
}

// Database Schema definition for Gemini
const DB_SCHEMA = `
We have a MySQL database named "weather_report" with 4 tables:

1. Table: current_weather (Current weather metrics for cities)
Columns:
- location_name VARCHAR(255) (e.g. 'ajmer', 'bangalore', 'bhopal', 'chennai', 'kota', etc.)
- location_region VARCHAR(255)
- location_country VARCHAR(255)
- location_lat DECIMAL(9, 6)
- location_lon DECIMAL(9, 6)
- location_tz_id VARCHAR(100)
- location_localtime DATETIME
- current_temp_c DECIMAL(5, 2)
- current_temp_f DECIMAL(5, 2)
- current_is_day TINYINT (1 for day, 0 for night)
- current_condition_text VARCHAR(255) (e.g. 'Partly cloudy', 'Sunny', 'Mist')
- current_wind_kph DECIMAL(5, 2)
- current_wind_dir VARCHAR(50)
- current_pressure_mb DECIMAL(6, 1)
- current_precip_mm DECIMAL(6, 2)
- current_humidity INT
- current_cloud INT
- current_feelslike_c DECIMAL(5, 2)
- current_vis_km DECIMAL(5, 2)
- current_uv DECIMAL(4, 1)
- current_aqi_co DECIMAL(12, 6)
- current_aqi_no2 DECIMAL(12, 6)
- current_aqi_o3 DECIMAL(12, 6)
- current_aqi_so2 DECIMAL(12, 6)
- current_aqi_pm2_5 DECIMAL(12, 6)
- current_aqi_pm10 DECIMAL(12, 6)
- current_aqi_us_epa_index INT (AQI index: 1=Good, 2=Moderate, 3=Unhealthy for sensitive groups, 4=Unhealthy, 5=Very Unhealthy, 6=Hazardous)

2. Table: forecast_day (Daily weather forecasts, astronomical data, and average AQI)
Columns:
- location_name VARCHAR(255)
- forecast_date DATE (Format: YYYY-MM-DD)
- day_maxtemp_c DECIMAL(5, 2)
- day_mintemp_c DECIMAL(5, 2)
- day_avgtemp_c DECIMAL(5, 2)
- day_maxwind_kph DECIMAL(5, 2)
- day_totalprecip_mm DECIMAL(6, 2)
- day_avgvis_km DECIMAL(5, 2)
- day_avghumidity INT
- day_will_it_rain TINYINT
- day_chance_of_rain INT
- day_condition_text VARCHAR(255)
- day_uv DECIMAL(4, 1)
- astro_sunrise VARCHAR(20) (e.g. '05:57 AM')
- astro_sunset VARCHAR(20) (e.g. '06:26 PM')
- astro_moonrise VARCHAR(20)
- astro_moonset VARCHAR(20)
- astro_moon_phase VARCHAR(50)
- astro_moon_illumination INT
- day_aqi_pm2_5 DECIMAL(12, 6)
- day_aqi_pm10 DECIMAL(12, 6)
- day_aqi_us_epa_index INT

3. Table: forecast_hour (Hourly weather forecast metrics)
Columns:
- location_name VARCHAR(255)
- hour_time DATETIME (Format: YYYY-MM-DD HH:MM:SS)
- hour_temp_c DECIMAL(5, 2)
- hour_is_day TINYINT
- hour_condition_text VARCHAR(255)
- hour_wind_kph DECIMAL(5, 2)
- hour_humidity INT
- hour_cloud INT
- hour_feelslike_c DECIMAL(5, 2)
- hour_will_it_rain TINYINT
- hour_chance_of_rain INT
- hour_vis_km DECIMAL(5, 2)
- hour_aqi_pm2_5 DECIMAL(12, 6)
- hour_aqi_pm10 DECIMAL(12, 6)

4. Table: master_report (Denormalized table containing a merge of current, daily, and hourly parameters)
Columns are a combination of current, forecast_day, and forecast_hour, grouped hourly.
`;

// Helper to clean SQL responses from Gemini
function cleanSQL(sqlText) {
  let cleaned = sqlText.trim();
  // Remove markdown code blocks if present
  if (cleaned.startsWith("```")) {
    cleaned = cleaned.replace(/^```sql\s*/i, "").replace(/^```\s*/, "").replace(/```$/, "").trim();
  }
  // Ensure we only execute SELECT queries
  if (!cleaned.toUpperCase().startsWith("SELECT")) {
    throw new Error("Only SELECT queries are allowed for security reasons.");
  }
  return cleaned;
}

// Endpoint: Chatbot
app.post("/api/chat", async (req, res) => {
  const { message, history } = req.body;
  if (!message) {
    return res.status(400).json({ error: "Message is required" });
  }

  try {
    const activeCitiesList = TRACKED_CITIES.join(", ");

    // Format history for context
    let formattedHistory = "";
    if (history && Array.isArray(history)) {
      formattedHistory = history
        .map((h) => `${h.sender === "user" ? "User" : "Assistant"}: ${h.text}`)
        .join("\n");
    }

    // Step 1: Classify user query, enforce city constraints, and generate SQL or direct answer
    const textToSqlPrompt = `
You are an expert MySQL query assistant and conversation router for a weather database project.
The weather database "weather_report" has the following schema:
${DB_SCHEMA}

Current conversation history:
${formattedHistory}

CRITICAL RULES:
1. The database ONLY contains weather data for the following specific cities: ${activeCitiesList}.
2. If the user asks about the weather, temperature, AQI, metrics, or comparisons of a city that is NOT in this list (or asks a general question about a specific untracked city), you must NOT query the database and must NOT make up any information. Instead, respond immediately with:
   ANSWER: The city [City Name] is not in our weather dataset. Currently, we only track: ${activeCitiesList}.
3. If the question requires querying the database tables for tracked cities to retrieve specific numbers, averages, comparisons, lists, or weather reports, respond with:
   QUERY: <write a single executable MySQL SELECT query that retrieves ONLY the data needed to answer the question. No markdown code blocks, just raw SQL.>
4. If the question is a general greeting, weather concept explanation (e.g. why AQI is high, how wind is measured, etc.), or a general forensic analysis that does not query specific database records, respond with:
   ANSWER: <write a short, direct conversational answer. Keep it very concise (1-2 sentences).>

User Question: "${message}"
Decision:`;

    console.log(`[Chatbot] Routing user question: "${message}"`);

    const sqlResponse = await ai.chat.completions.create({
  model: "llama-3.3-70b-versatile",
  messages: [
    {
      role: "user",
      content: textToSqlPrompt,
    },
  ],
  temperature: 0,
});

const responseText =
  sqlResponse.choices?.[0]?.message?.content?.trim() || "";
    console.log(`[Chatbot] Router response: "${responseText}"`);

    if (responseText.toUpperCase().startsWith("QUERY:")) {
      const sqlQueryText = responseText.substring(6).trim();
      let sqlQuery;
      try {
        sqlQuery = cleanSQL(sqlQueryText);
        console.log(`[Chatbot] Cleaned SQL: "${sqlQuery}"`);
      } catch (cleanErr) {
        console.error("[Chatbot] SQL cleaning failed:", cleanErr);
        return res.json({
          response: `I'm sorry, I couldn't safely run that database query.`,
          sqlQuery: null
        });
      }

      // Execute SQL against Database
      let queryResults;
      try {
        const [rows] = await pool.query(sqlQuery);
        queryResults = rows;
        console.log(`[Chatbot] Query executed successfully. Returned ${queryResults.length} rows.`);
      } catch (dbErr) {
        console.error("[Chatbot] Database query execution failed:", dbErr);
        return res.json({
          response: `I encountered an error executing the query on the database.`,
          sqlQuery: sqlQuery
        });
      }

      // Step 3: Formulate final direct response using results
      const answerPrompt = `
You are a direct, concise weather project assistant.
The user asked: "${message}"

The MySQL query executed returned the following database results:
${JSON.stringify(queryResults, null, 2)}

Provide a short, simple, direct answer to the user's question based on these results.
Rules:
1. Give a direct answer (usually 1 or 2 sentences max). Do not write a long paragraph or introduce unnecessary conversational filler.
2. Focus on the core numbers or insights requested.
3. If no matching data was found, state that directly and concisely.

Answer:`;

      let answerText;

      try {
        const answerResponse = await ai.chat.completions.create({
  model: "llama-3.3-70b-versatile",
  messages: [
    {
      role: "user",
      content: answerPrompt,
    },
  ],
  temperature: 0,
});

answerText =
  answerResponse.choices?.[0]?.message?.content?.trim() || "";
      } catch (err) {
        console.error("Gemini answer generation failed:", err);
        answerText =
          queryResults.length > 0
            ? JSON.stringify(queryResults, null, 2)
            : "No matching data found.";
      }

      res.json({
        response: answerText,
        sqlQuery: sqlQuery
      });
    } else {
      // It is a direct ANSWER (starts with "ANSWER:" or we treat it as an answer)
      let answerText = responseText;
      if (responseText.toUpperCase().startsWith("ANSWER:")) {
        answerText = responseText.substring(7).trim();
      }
      console.log(`[Chatbot] Returning direct answer: "${answerText}"`);
      res.json({
        response: answerText,
        sqlQuery: null
      });
    }

  } catch (error) {
    console.error("[Chatbot] System Error:", error);
    res.status(500).json({ error: "Internal server error during chatbot process." });
  }
});

function runPipeline() {
  const scriptPath = path.join(__dirname, "../database/pipeline.py");
  const dbDir = path.join(__dirname, "../database");

  return new Promise((resolve, reject) => {
    const child = spawn("python3", ["-u", scriptPath], {
      cwd: dbDir,
      env: { ...process.env, PYTHONUNBUFFERED: "1" },
    });

    let stdout = "";
    let stderr = "";

    child.stdout.on("data", (chunk) => {
      const text = chunk.toString();
      stdout += text;
      process.stdout.write(`[Pipeline] ${text}`);
    });

    child.stderr.on("data", (chunk) => {
      const text = chunk.toString();
      stderr += text;
      process.stderr.write(`[Pipeline] ${text}`);
    });

    child.on("error", (err) => reject(err));

    child.on("close", (code) => {
      if (code === 0) {
        console.log("[Refresh Database] Pipeline succeeded.");
        resolve(stdout);
      } else {
        reject(new Error(stderr.trim() || `Pipeline exited with code ${code}`));
      }
    });
  });
}

// Endpoint: Refresh database (fetch API -> CSV -> SQL -> dedupe)
app.post("/api/refresh-database", async (req, res) => {
  try {
    console.log("[Refresh Database] Running weather data pipeline...");
    const pipelineOutput = await runPipeline();
    res.json({ success: true, message: "Database updated successfully.", pipelineOutput });
  } catch (error) {
    console.error("[Refresh Database] Error:", error.message);
    res.status(500).json({
      success: false,
      error: error.message || "Failed to update database.",
    });
  }
});

// Start Server
const server = app.listen(PORT, () => {
  console.log(`Express server is running on http://localhost:${PORT}`);
});

// Gracefully handle address already in use (EADDRINUSE)
server.on("error", (err) => {
  if (err.code === "EADDRINUSE") {
    console.error(`\n[Error] Port ${PORT} is already in use!`);
    console.error(`Please check if another backend server is running.`);
    console.error(`You can kill the process on port ${PORT} using: kill -9 $(lsof -t -i:${PORT})\n`);
    process.exit(1);
  } else {
    console.error("Server error:", err);
  }
});