<script lang="ts">
	import { page } from '$app/state';
	import { onMount } from 'svelte';
	import { getPoll, vote as submitVote, closePoll, deletePoll, subscribePoll } from '$lib/api';
	import type { Poll } from '$lib/api';
	import VoteCalendar from '$lib/components/VoteCalendar.svelte';
	import VoteGrid from '$lib/components/VoteGrid.svelte';

	let poll: Poll | null = $state(null);
	let loading = $state(true);
	let error = $state('');
	let voterName = $state('');
	let editingVotes: Map<string, 'yes' | 'no' | 'maybe'> | null = $state(null);
	let submitting = $state(false);
	let editToken: string | null = $state(null);
	let currentParticipantId: string | null = $state(null);
	let showSuccess = $state(false);
	let copied = $state(false);

	let pollId = $derived(page.params.id!);
	let adminToken = $derived(localStorage.getItem(`yado-admin-${pollId}`));

	const CHOICE_CYCLE: ('yes' | 'maybe' | 'no')[] = ['no', 'yes', 'maybe'];

	function cycleChoice(current: 'yes' | 'no' | 'maybe'): 'yes' | 'no' | 'maybe' {
		const idx = CHOICE_CYCLE.indexOf(current);
		return CHOICE_CYCLE[(idx + 1) % CHOICE_CYCLE.length];
	}

	function toggleVote(dateOptionId: string) {
		if (!editingVotes) return;
		const current = editingVotes.get(dateOptionId) ?? 'no';
		const next = new Map(editingVotes);
		next.set(dateOptionId, cycleChoice(current));
		editingVotes = next;
	}

	function setVotes(updates: Map<string, 'yes' | 'no' | 'maybe'>) {
		if (!editingVotes) return;
		const next = new Map(editingVotes);
		for (const [id, choice] of updates) {
			next.set(id, choice);
		}
		editingVotes = next;
	}

	function startVoting() {
		if (!poll) return;
		editingVotes = new Map(poll.date_options.map((o) => [o.id, 'no' as const]));

		const stored = localStorage.getItem(`yado-vote-${pollId}`);
		if (stored) {
			try {
				const data = JSON.parse(stored);
				editToken = data.editToken;
				currentParticipantId = data.participantId ?? null;
				voterName = data.name;
				for (const [optId, choice] of Object.entries(data.votes)) {
					editingVotes.set(optId, choice as 'yes' | 'no' | 'maybe');
				}
				editingVotes = new Map(editingVotes);
			} catch {
				// ignore corrupt data
			}
		}
	}

	async function handleVoteSubmit() {
		if (!poll || !editingVotes) return;
		if (!voterName.trim()) {
			error = 'Enter your name';
			return;
		}

		submitting = true;
		error = '';
		try {
			const votes = [...editingVotes.entries()]
				.filter(([, choice]) => choice !== 'no')
				.map(([date_option_id, choice]) => ({ date_option_id, choice }));

			const res = await submitVote(pollId, {
				name: voterName.trim(),
				edit_token: editToken,
				votes
			});

			const voteData: Record<string, string> = {};
			for (const [k, v] of editingVotes) voteData[k] = v;
			localStorage.setItem(
				`yado-vote-${pollId}`,
				JSON.stringify({ editToken: res.edit_token, participantId: res.participant_id, name: voterName.trim(), votes: voteData })
			);
			editToken = res.edit_token;
			currentParticipantId = res.participant_id;

			showSuccess = true;
			setTimeout(() => (showSuccess = false), 3000);

			poll = await getPoll(pollId);
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to submit vote';
		} finally {
			submitting = false;
		}
	}

	async function handleClose() {
		if (!adminToken || !poll) return;
		try {
			poll = await closePoll(pollId, adminToken);
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to close poll';
		}
	}

	async function handleDelete() {
		if (!adminToken) return;
		if (!confirm('Delete this poll permanently?')) return;
		try {
			await deletePoll(pollId, adminToken);
			window.location.href = '/';
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to delete poll';
		}
	}

	function copyLink() {
		navigator.clipboard.writeText(window.location.href);
		copied = true;
		setTimeout(() => (copied = false), 2000);
	}

	onMount(() => {
		getPoll(pollId)
			.then((p) => {
				poll = p;
				if (!p.closed) startVoting();
			})
			.catch((e) => (error = e instanceof Error ? e.message : 'Poll not found'))
			.finally(() => (loading = false));

		const sub = subscribePoll(pollId, (updated) => {
			poll = updated;
		});
		return () => sub.close();
	});
</script>

{#if loading}
	<div class="flex justify-center py-20">
		<div class="h-10 w-10 animate-spin rounded-full border-4 border-blue-600 border-t-transparent"></div>
	</div>
{:else if !poll}
	<div class="rounded-2xl border border-red-200 bg-red-50 p-8 text-center">
		<p class="text-lg font-semibold text-red-700">{error || 'Poll not found'}</p>
	</div>
{:else}
	<div class="space-y-6">
		<!-- Header -->
		<div>
			<div class="flex items-start justify-between gap-4">
				<div>
					<h1 class="text-3xl font-bold tracking-tight text-slate-900">{poll.title}</h1>
					{#if poll.description}
						<p class="mt-2 text-lg text-slate-500">{poll.description}</p>
					{/if}
				</div>
				{#if poll.closed}
					<span class="shrink-0 rounded-full bg-red-100 px-3 py-1 text-sm font-semibold text-red-700">Closed</span>
				{/if}
			</div>
		</div>

		<!-- Share link -->
		<div class="flex items-center gap-2">
			<input
				type="text"
				readonly
				value={typeof window !== 'undefined' ? window.location.href : ''}
				class="flex-1 rounded-lg border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm text-slate-500 font-mono"
			/>
			<button
				type="button"
				class="rounded-lg bg-slate-200 px-4 py-2.5 text-sm font-medium text-slate-700 hover:bg-slate-300 transition-colors"
				onclick={copyLink}>{copied ? 'Copied!' : 'Copy link'}</button
			>
		</div>

		<!-- Calendar view -->
		<div class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
			{#if editingVotes}
				<h2 class="mb-4 text-sm font-semibold text-slate-500 uppercase tracking-wide">Your availability</h2>
			{:else}
				<h2 class="mb-4 text-sm font-semibold text-slate-500 uppercase tracking-wide">Overview</h2>
			{/if}
			<VoteCalendar
				dateOptions={poll.date_options}
				participants={poll.participants}
				editing={editingVotes}
				onSetVotes={setVotes}
			/>
		</div>

		<!-- Vote grid -->
		<div class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
			<h2 class="mb-4 text-sm font-semibold text-slate-500 uppercase tracking-wide">Responses</h2>
			<VoteGrid
				dateOptions={poll.date_options}
				participants={poll.participants}
				editing={editingVotes}
				editingParticipantId={currentParticipantId}
				editingName={voterName}
				onToggle={toggleVote}
				onSetVotes={setVotes}
			/>
		</div>

		<!-- Vote form -->
		{#if !poll.closed && editingVotes}
			<div class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
				<div class="flex flex-col sm:flex-row items-start sm:items-end gap-4">
					<div class="w-full sm:flex-1 sm:max-w-xs">
						<label for="voter-name" class="mb-1.5 block text-sm font-semibold text-slate-700">Your name</label>
						<input
							id="voter-name"
							type="text"
							bind:value={voterName}
							placeholder="Enter your name"
							class="w-full rounded-lg border border-slate-200 px-3.5 py-2.5 text-slate-900 placeholder-slate-400 shadow-sm focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 focus:outline-none transition-shadow"
						/>
					</div>
					<button
						type="button"
						disabled={submitting}
						class="rounded-lg bg-blue-600 px-6 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-blue-700 disabled:opacity-50 transition-colors"
						onclick={handleVoteSubmit}
					>
						{submitting ? 'Submitting...' : editToken ? 'Update Vote' : 'Submit Vote'}
					</button>
				</div>
				{#if error}
					<div class="mt-3 rounded-lg bg-red-50 border border-red-200 px-4 py-2.5 text-sm text-red-700">{error}</div>
				{/if}
			</div>
		{/if}

		{#if showSuccess}
			<div class="rounded-lg bg-emerald-50 border border-emerald-200 px-4 py-3 text-sm font-medium text-emerald-700">
				Vote submitted successfully!
			</div>
		{/if}

		<!-- Admin controls -->
		{#if adminToken}
			<div class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
				<h3 class="mb-3 text-sm font-semibold text-slate-500 uppercase tracking-wide">Admin</h3>
				<div class="flex gap-3">
					{#if !poll.closed}
						<button
							type="button"
							class="rounded-lg border border-amber-200 bg-amber-50 px-4 py-2 text-sm font-medium text-amber-700 hover:bg-amber-100 transition-colors"
							onclick={handleClose}>Close Poll</button
						>
					{/if}
					<button
						type="button"
						class="rounded-lg border border-red-200 bg-red-50 px-4 py-2 text-sm font-medium text-red-700 hover:bg-red-100 transition-colors"
						onclick={handleDelete}>Delete Poll</button
					>
				</div>
			</div>
		{/if}
	</div>
{/if}
