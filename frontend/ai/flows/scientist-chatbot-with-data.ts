
'use server';

/**
 * @fileOverview A chatbot flow that uses a tool to incorporate external Argo data when relevant to provide detailed and accurate responses suitable for experts.
 *
 * - scientistChatbotWithData - A function that handles the chatbot interaction in scientist mode.
 * - ScientistChatbotWithDataInput - The input type for the scientistChatbotWithData function.
 * - ScientistChatbotWithDataOutput - The return type for the scientistChatbotWithData function.
 */

import {ai} from '@/ai/genkit';
import {z} from 'genkit';
import { getArgoFloatById } from '@/lib/argo-data-service';

const ScientistChatbotWithDataInputSchema = z.object({
  query: z.string().describe('The query from the user.'),
});
export type ScientistChatbotWithDataInput = z.infer<
  typeof ScientistChatbotWithDataInputSchema
>;

const ScientistChatbotWithDataOutputSchema = z.object({
  response: z.string().describe('The response from the chatbot.'),
});
export type ScientistChatbotWithDataOutput = z.infer<
  typeof ScientistChatbotWithDataOutputSchema
>;

export async function scientistChatbotWithData(
  input: ScientistChatbotWithDataInput
): Promise<ScientistChatbotWithDataOutput> {
  return scientistChatbotWithDataFlow(input);
}

const getArgoDataTool = ai.defineTool({
  name: 'getArgoData',
  description: 'Retrieves specific Argo float data based on its ID. Use this to answer questions about a particular float.',
  inputSchema: z.object({
    floatId: z.string().describe('The ID of the Argo float, e.g., "AF-2901998".'),
  }),
  outputSchema: z.string().describe('A JSON string of the Argo float data, or a "not found" message.'),
},
async ({ floatId }) => {
    const float = getArgoFloatById(floatId);
    if (!float) {
      return `Argo float with ID "${floatId}" not found.`;
    }
    return JSON.stringify(float);
  }
);

const prompt = ai.definePrompt({
  name: 'scientistChatbotWithDataPrompt',
  input: {schema: ScientistChatbotWithDataInputSchema},
  output: {schema: ScientistChatbotWithDataOutputSchema},
  tools: [getArgoDataTool],
  prompt: `You are a helpful chatbot assisting scientists with Argo float data.

  The user is in scientist mode, so provide detailed and accurate responses using precise terminology.
  Use the getArgoData tool when the user's query requires accessing data for a specific Argo float by its ID.
  If the user asks a general question, provide a general answer. If they ask about a specific float, use the tool.

  User query: {{{query}}}
  `,
});

const scientistChatbotWithDataFlow = ai.defineFlow(
  {
    name: 'scientistChatbotWithDataFlow',
    inputSchema: ScientistChatbotWithDataInputSchema,
    outputSchema: ScientistChatbotWithDataOutputSchema,
  },
  async input => {
    const {output} = await prompt(input);
    return output!;
  }
);
