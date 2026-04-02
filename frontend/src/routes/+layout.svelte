<script lang="ts">
	import '../app.css';
	import favicon from '$lib/assets/favicon.svg';

	let { children } = $props();
</script>

<svelte:head>
	<link rel="icon" href={favicon} />
	<title>Yado</title>
	<link rel="preconnect" href="https://fonts.googleapis.com" />
	<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin="anonymous" />
	<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet" />
</svelte:head>

<div class="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50" style="font-family: 'Inter', system-ui, sans-serif;">
	<header class="border-b border-slate-200 bg-white/80 backdrop-blur-sm">
		<div class="mx-auto max-w-4xl px-4 py-5">
			<a href="/" class="group flex items-center gap-2">
				<span class="text-2xl font-bold tracking-tight text-slate-900">Yet Another Doodle</span>
			</a>
		</div>
	</header>
	<main class="mx-auto max-w-4xl px-4 py-10">
		{@render children()}
	</main>
</div>
