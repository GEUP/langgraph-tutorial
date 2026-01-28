import { graph as simpleNodeExample } from './L1/01-simple-node.js';
import { graph as parallelExecutionExample } from './L1/02-parallel-execution.js';
import { graph as conditionalEdgesExample } from './L1/03-conditional-edges.js';
import { graph as memoryExample } from './L1/04-memory.js';
import { graph as interruptsExample } from './L1/05-interrupts.js';

import { fileURLToPath } from 'url';
import path from 'path';
import fs from 'fs/promises';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const PREVIEW_IMAGE_PATH = path.resolve(__dirname, '..', 'preview');

const graphs = {
  simpleNodeExample,
  parallelExecutionExample,
  conditionalEdgesExample,
  memoryExample,
  interruptsExample,
};

await fs.mkdir(PREVIEW_IMAGE_PATH, { recursive: true });

Promise.all(
  Object.entries(graphs).map(async ([key, value]) => {
    const graph = await value.getGraphAsync();
    const mermaidImage = await graph.drawMermaidPng();
    const outputPath = path.join(PREVIEW_IMAGE_PATH, `${key}.png`);
    const buffer = Buffer.from(await mermaidImage.arrayBuffer());
    await fs.writeFile(outputPath, buffer);
  })
);
