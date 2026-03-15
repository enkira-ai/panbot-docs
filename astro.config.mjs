import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';

export default defineConfig({
	site: process.env.SITE_URL || 'https://docs.panbot.ai',
	base: process.env.BASE_PATH || '/',
	vite: {
		server: {
			allowedHosts: ['docs.panbot.ai'],
		},
	},
	integrations: [
		starlight({
			title: 'Panbot Documentation',
			// Disable built-in Pagefind search — replaced by Lunr.js
			pagefind: false,
			components: {
				Header: './src/overrides/Header.astro',
			},
			sidebar: [
				{
					label: 'Architecture',
					autogenerate: { directory: 'architecture' },
				},
				{
					label: 'Guides',
					autogenerate: { directory: 'guides' },
				},
				{
					label: 'Reference',
					autogenerate: { directory: 'reference' },
				},
			],
		}),
	],
});
