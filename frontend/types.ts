import { z } from 'zod';

const externalUrl = z.url().refine(value => value.startsWith('https://') || value.startsWith('http://'));
export const projectSchema = z.object({
  slug: z.string(), title: z.string(), description: z.string(), technologies: z.array(z.string()),
  repo_url: externalUrl.nullable(), live_url: externalUrl.nullable(), image: z.string().nullable(),
});
export const contentSchema = z.object({
  author: z.string(), year: z.number(), projects: z.array(projectSchema),
  cv: z.object({
    headline: z.string(), summary: z.string(),
    contact: z.object({ email: z.string(), linkedin: z.string(), github: z.string(), location: z.string(), portfolio: externalUrl }),
    skills: z.array(z.string()), languages: z.array(z.string()),
    roles: z.array(z.object({ date: z.string(), role: z.string(), company: z.string(), summary: z.string(), points: z.array(z.string()) })),
    previous_roles: z.array(z.object({ date: z.string(), text: z.string() })),
    certifications: z.array(z.object({ name: z.string(), issuer: z.string(), url: externalUrl.optional() })),
    education: z.array(z.string()), education_links: z.record(z.string(), externalUrl),
  }),
});
export type Content = z.infer<typeof contentSchema>;
export type Project = z.infer<typeof projectSchema>;
export const pageSchema = z.enum(['home', 'about', 'projects']);
export type Page = z.infer<typeof pageSchema>;
export const coldfileSchema = z.object({
  episode_count: z.number(),
  latest: z.object({ video_id: z.string().regex(/^[\w-]{11}$/), title: z.string(), published: z.string() }),
});
export const statusSchema = z.object({
  checked_at: z.string(),
  services: z.array(z.object({ id: z.string(), name: z.string(), desc: z.string(), url: externalUrl,
    status: z.enum(['up', 'idle', 'down']), latency_ms: z.number().nullable().optional(), detail: z.string().optional() })),
});
export const githubSchema = z.object({ username: z.string(), total: z.number(), _stale: z.boolean().optional(), weeks: z.array(z.object({
  contributionDays: z.array(z.object({ date: z.string(), contributionCount: z.number().int().nonnegative(), weekday: z.number().int().min(0).max(6) })),
})) });
export type GitHubData = z.infer<typeof githubSchema>;
export const apologySchema = z.object({ apology: z.string(), meta: z.string() });
export const chatMetaSchema = z.object({
  source: z.string(), model: z.string().optional(), embedding_provider: z.string().nullable().optional(),
  embed_ms: z.number().nullable().optional(), ai_ms: z.number().nullable().optional(),
  sources: z.array(z.object({ filename: z.string(), score: z.number(), excerpt: z.string() })).optional(),
});
export type ChatMeta = z.infer<typeof chatMetaSchema>;
export const chatEventSchema = z.discriminatedUnion('type', [
  z.object({ type: z.literal('stage'), stage: z.string() }),
  chatMetaSchema.extend({ type: z.literal('meta') }),
  z.object({ type: z.literal('token'), t: z.string() }),
  z.object({ type: z.literal('done') }),
]);
export const chatAnswerSchema = chatMetaSchema.extend({ answer: z.string() });
