
'use server';

/**
 * @fileOverview Generates simple, easy-to-understand responses for the Argo Chatbot in education mode.
 *
 * - generateEducationalResponse - A function that generates educational responses with example questions.
 * - EducationalResponseInput - The input type for the generateEducationalResponse function.
 * - EducationalResponseOutput - The return type for the generateEducationalResponse function.
 */

import {ai} from '@/ai/genkit';
import {z} from 'genkit';

const EducationalResponseInputSchema = z.object({
  query: z.string().describe('The user query.'),
});
export type EducationalResponseInput = z.infer<typeof EducationalResponseInputSchema>;

const EducationalResponseOutputSchema = z.object({
  response: z.string().describe('The simple, easy-to-understand response to the query.'),
  exampleQuestions: z.array(z.string()).describe('Example questions to guide the user.'),
});
export type EducationalResponseOutput = z.infer<typeof EducationalResponseOutputSchema>;

export async function generateEducationalResponse(
  input: EducationalResponseInput
): Promise<EducationalResponseOutput> {
  return educationalChatbotFlow(input);
}

const educationalChatbotPrompt = ai.definePrompt({
  name: 'educationalChatbotPrompt',
  input: {schema: EducationalResponseInputSchema},
  output: {schema: EducationalResponseOutputSchema},
  prompt: `You are an educational chatbot designed to provide simple, easy-to-understand responses to user queries about ocean data.
  Provide example questions to guide the user.

  User Query: {{{query}}}

  Response:`,
});

const educationalChatbotFlow = ai.defineFlow(
  {
    name: 'educationalChatbotFlow',
    inputSchema: EducationalResponseInputSchema,
    outputSchema: EducationalResponseOutputSchema,
  },
  async input => {
    const {output} = await educationalChatbotPrompt(input);
    return output!;
  }
);
