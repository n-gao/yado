<script lang="ts">
	import { goto } from '$app/navigation';
	import Calendar from '$lib/components/Calendar.svelte';
	import { createPoll } from '$lib/api';
	import type { PollCreated } from '$lib/api';

	let title = $state('');
	let description = $state('');
	let selectedDates: Set<string> = $state(new Set());
	let submitting = $state(false);
	let error = $state('');
	let created: PollCreated | null = $state(null);

	function getShareLink(c: PollCreated): string {
		return `${window.location.origin}/poll/${c.id}`;
	}
	function getAdminLink(c: PollCreated): string {
		return `${window.location.origin}/poll/${c.id}/admin/${c.admin_token}`;
	}

	async function handleSubmit() {
		if (!title.trim()) {
			error = 'Title is required';
			return;
		}
		if (selectedDates.size === 0) {
			error = 'Select at least one date';
			return;
		}

		submitting = true;
		error = '';
		try {
			const sorted = [...selectedDates].sort();
			created = await createPoll({
				title: title.trim(),
				description: description.trim(),
				timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
				date_options: sorted.map((d) => ({ date: d }))
			});

			localStorage.setItem(`yado-admin-${created.id}`, created.admin_token);
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to create poll';
		} finally {
			submitting = false;
		}
	}

	let copiedShare = $state(false);
	let copiedAdmin = $state(false);

	function copy(text: string, which: 'share' | 'admin') {
		navigator.clipboard.writeText(text);
		if (which === 'share') { copiedShare = true; setTimeout(() => copiedShare = false, 2000); }
		else { copiedAdmin = true; setTimeout(() => copiedAdmin = false, 2000); }
	}
</script>

<div class="mx-auto max-w-xl">
	{#if created}
		<div class="rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
			<div class="mb-6 text-center">
				<div class="mx-auto mb-3 flex h-14 w-14 items-center justify-center rounded-full bg-green-100">
					<svg class="h-7 w-7 text-green-600" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
						<path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12.75l6 6 9-13.5" />
					</svg>
				</div>
				<h1 class="text-2xl font-bold text-slate-900">Poll Created!</h1>
				<p class="mt-1 text-slate-500">Share the link below with your participants</p>
			</div>

			<div class="space-y-5">
				<div>
					<p class="mb-1.5 text-sm font-semibold text-slate-700">Participant link</p>
					<div class="flex items-center gap-2">
						<input
							type="text"
							readonly
							value={getShareLink(created)}
							class="flex-1 rounded-lg border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm text-slate-600 font-mono"
						/>
						<button
							type="button"
							class="rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-medium text-white shadow-sm hover:bg-blue-700 transition-colors"
							onclick={() => copy(getShareLink(created!), 'share')}>{copiedShare ? 'Copied!' : 'Copy'}</button
						>
					</div>
				</div>

				<div>
					<p class="mb-1.5 text-sm font-semibold text-slate-700">Admin link <span class="font-normal text-slate-400">(close or delete)</span></p>
					<div class="flex items-center gap-2">
						<input
							type="text"
							readonly
							value={getAdminLink(created)}
							class="flex-1 rounded-lg border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm text-slate-600 font-mono"
						/>
						<button
							type="button"
							class="rounded-lg bg-slate-200 px-4 py-2.5 text-sm font-medium text-slate-700 hover:bg-slate-300 transition-colors"
							onclick={() => copy(getAdminLink(created!), 'admin')}>{copiedAdmin ? 'Copied!' : 'Copy'}</button
						>
					</div>
					<p class="mt-1.5 text-xs text-slate-400">Save this link — anyone with it can manage the poll.</p>
				</div>

				<button
					type="button"
					class="w-full rounded-lg bg-blue-600 px-4 py-3 font-semibold text-white shadow-sm hover:bg-blue-700 transition-colors"
					onclick={() => goto(`/poll/${created!.id}`)}
				>
					Go to Poll
				</button>
			</div>
		</div>
	{:else}
		<div class="rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
			<h1 class="mb-1 text-2xl font-bold text-slate-900">Create a Poll</h1>
			<p class="mb-6 text-slate-500">Find a date that works for everyone</p>

			<form onsubmit={(e) => { e.preventDefault(); handleSubmit(); }}>
				<div class="mb-5">
					<label for="title" class="mb-1.5 block text-sm font-semibold text-slate-700">Title</label>
					<input
						id="title"
						type="text"
						bind:value={title}
						placeholder="e.g. Team dinner"
						class="w-full rounded-lg border border-slate-200 px-3.5 py-2.5 text-slate-900 placeholder-slate-400 shadow-sm focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 focus:outline-none transition-shadow"
					/>
				</div>

				<div class="mb-6">
					<label for="desc" class="mb-1.5 block text-sm font-semibold text-slate-700"
						>Description <span class="font-normal text-slate-400">(optional)</span></label
					>
					<textarea
						id="desc"
						bind:value={description}
						rows={2}
						placeholder="Any extra details..."
						class="w-full rounded-lg border border-slate-200 px-3.5 py-2.5 text-slate-900 placeholder-slate-400 shadow-sm focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 focus:outline-none transition-shadow"
					></textarea>
				</div>

				<div class="mb-6">
					<h2 class="mb-3 text-sm font-semibold text-slate-700">
						Pick dates <span class="font-normal text-slate-400">(click, shift+click, or drag)</span>
					</h2>
					<Calendar selected={selectedDates} onchange={(d) => (selectedDates = d)} />
				</div>

				{#if error}
					<div class="mb-4 rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700">{error}</div>
				{/if}

				<button
					type="submit"
					disabled={submitting}
					class="w-full rounded-lg bg-blue-600 px-4 py-3 font-semibold text-white shadow-sm hover:bg-blue-700 disabled:opacity-50 transition-colors"
				>
					{submitting ? 'Creating...' : 'Create Poll'}
				</button>
			</form>
		</div>
	{/if}
</div>
