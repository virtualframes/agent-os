const fastify = require('fastify')({ logger: true });

// Dynamically import node-fetch
const fetch = (...args) => import('node-fetch').then(({default: fetch}) => fetch(...args));

// Register a health check route
fastify.get('/health', async (request, reply) => {
  return { ok: true };
});

// Endpoint for memory context loading
fastify.get('/export/qme/leaderboard.json', async (request, reply) => {
    // Return an empty array as a placeholder to prevent client-side errors
    return [];
});

// Register MCP routes
fastify.register(async function (fastify, options) {
    // New MCP orchestration routes
    fastify.post('/mcp/command', async (req, reply) => {
      const { command, context } = req.body;

      // Route to Python MCP router
      const mcpResp = await fetch('http://127.0.0.1:8090/mcp/route', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ command, context })
      });

      const data = await mcpResp.json();
      reply.send(data);
    });

    // Memory persistence endpoints
    fastify.post('/memory/ingest', async (req, reply) => {
      const { content, tags, source } = req.body;
      // Store in Neo4j via existing memory API
      // ...
      reply.send({ status: 'ok', message: 'ingested' });
    });
});


// Run the server
const start = async () => {
  try {
    await fastify.listen({ port: 8080 });
  } catch (err) {
    fastify.log.error(err);
    process.exit(1);
  }
};

start();