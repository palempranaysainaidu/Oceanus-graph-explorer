
"use server";
/**
 * @fileOverview A flow for generating insights about a single Argo float using Groq API.
 *
 * - generateFloatInsights - A function that takes float data and returns an analysis.
 * - FloatInsightsInput - The input type for the generateFloatInsights function.
 * - FloatInsightsOutput - The return type for the generateFloatInsights function.
 */

import { z } from 'zod';

// We need to define the schema for the float data passed to the flow.
// This is different from the main ArgoFloat type which now includes historical data.
const FloatDataForInsightSchema = z.object({
  id: z.string(),
  lastReported: z.string(),
  latitude: z.number(),
  longitude: z.number(),
  temperature: z.number(),
  salinity: z.number(),
  pressure: z.number(),
});


const FloatInsightsInputSchema = z.object({
  floatData: FloatDataForInsightSchema.describe("The data for the Argo float to be analyzed."),
});
export type FloatInsightsInput = z.infer<typeof FloatInsightsInputSchema>;

const FloatInsightsOutputSchema = z.object({
  insights: z.string().describe('A concise analysis of the provided Argo float data.'),
});
export type FloatInsightsOutput = z.infer<typeof FloatInsightsOutputSchema>;

export async function generateFloatInsights(input: FloatInsightsInput): Promise<FloatInsightsOutput> {
  const groqApiKey = process.env.GROQ_API_KEY;

  if (!groqApiKey) {
    throw new Error('GROQ_API_KEY is not configured');
  }

  const prompt = `You are an expert oceanographer providing a quick analysis of a single Argo float.
Based on the data provided, generate a short, insightful summary (2-3 sentences).
Focus on any notable readings (e.g., unusually high temperature, low salinity) and its general location.
Do not just list the data, interpret it.

Float Data:
- ID: ${input.floatData.id}
- Location: ${input.floatData.latitude}, ${input.floatData.longitude}
- Last Reported: ${input.floatData.lastReported}
- Temperature: ${input.floatData.temperature}°C
- Salinity: ${input.floatData.salinity} PSS
- Pressure: ${input.floatData.pressure} dbar

Provide only the analysis without any additional formatting or labels.`;

  try {
    const response = await fetch('https://api.groq.com/openai/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${groqApiKey}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        model: 'llama-3.3-70b-versatile',
        messages: [
          {
            role: 'user',
            content: prompt
          }
        ],
        temperature: 0.7,
        max_tokens: 500,
      }),
    });

    if (!response.ok) {
      throw new Error(`Groq API error: ${response.status} ${response.statusText}`);
    }

    const data = await response.json();
    const insights = data.choices[0]?.message?.content?.trim() || 'Unable to generate insights';

    return { insights };
  } catch (error) {
    console.error('Error calling Groq API:', error);
    throw new Error('Failed to generate float insights');
  }
}
