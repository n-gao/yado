<script lang="ts">
	import { page } from '$app/state';
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';

	onMount(() => {
		const pollId = page.params.id!;
		const token = page.params.token!;
		localStorage.setItem(`yado-admin-${pollId}`, token);
		goto(`/poll/${pollId}`, { replaceState: true });
	});
</script>

<div class="flex justify-center py-12">
	<div class="h-8 w-8 animate-spin rounded-full border-4 border-blue-500 border-t-transparent"></div>
</div>
