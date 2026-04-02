<script lang="ts">
	import { format, parseISO } from 'date-fns';
	import type { DateOption, Participant } from '$lib/api';

	type Choice = 'yes' | 'no' | 'maybe';

	interface Props {
		dateOptions: DateOption[];
		participants: Participant[];
		editing: Map<string, Choice> | null;
		editingParticipantId?: string | null;
		editingName?: string;
		onToggle?: (dateOptionId: string) => void;
		onSetVotes?: (updates: Map<string, Choice>) => void;
	}

	let { dateOptions, participants, editing, editingParticipantId = null, editingName = 'You', onToggle, onSetVotes }: Props = $props();

	// Other participants (exclude current user if editing)
	let otherParticipants = $derived(
		editing && editingParticipantId
			? participants.filter((p) => p.id !== editingParticipantId)
			: participants
	);

	let sortedOptions = $derived(
		[...dateOptions].sort((a, b) => a.date.localeCompare(b.date))
	);

	function choiceIcon(choice: string): string {
		if (choice === 'yes') return '\u2713';
		if (choice === 'maybe') return '?';
		return '\u2717';
	}

	function choiceColor(choice: string): string {
		if (choice === 'yes') return 'bg-emerald-100 text-emerald-700';
		if (choice === 'maybe') return 'bg-amber-100 text-amber-700';
		return 'bg-red-50 text-red-400';
	}

	function countYes(optId: string): number {
		return participants.filter((p) =>
			p.votes.some((v) => v.date_option_id === optId && v.choice === 'yes')
		).length;
	}

	function countMaybe(optId: string): number {
		return participants.filter((p) =>
			p.votes.some((v) => v.date_option_id === optId && v.choice === 'maybe')
		).length;
	}

	let bestCount = $derived(Math.max(0, ...sortedOptions.map((o) => countYes(o.id))));

	const CYCLE: Choice[] = ['no', 'yes', 'maybe'];
	function nextChoice(c: Choice): Choice {
		return CYCLE[(CYCLE.indexOf(c) + 1) % CYCLE.length];
	}

	let lastClicked: string | null = $state(null);
	let isDragging = $state(false);
	let dragChoice: Choice = $state('yes');

	function handlePointerDown(optId: string, e: PointerEvent) {
		if (!editing || !onToggle || !onSetVotes) return;
		e.preventDefault();

		if (e.shiftKey && lastClicked) {
			const ids = sortedOptions.map((o) => o.id);
			const a = ids.indexOf(lastClicked);
			const b = ids.indexOf(optId);
			const [start, end] = a < b ? [a, b] : [b, a];
			const current = editing.get(optId) ?? 'no';
			const choice = nextChoice(current);
			const updates = new Map<string, Choice>();
			for (let i = start; i <= end; i++) {
				updates.set(ids[i], choice);
			}
			onSetVotes(updates);
		} else {
			const current = editing.get(optId) ?? 'no';
			dragChoice = nextChoice(current);
			onSetVotes(new Map([[optId, dragChoice]]));
			isDragging = true;
		}
		lastClicked = optId;
	}

	function handlePointerEnter(optId: string) {
		if (!isDragging || !editing || !onSetVotes) return;
		onSetVotes(new Map([[optId, dragChoice]]));
	}

	function handlePointerUp() {
		isDragging = false;
	}
</script>

<!-- svelte-ignore a11y_no_static_element_interactions -->
<svelte:window onpointerup={handlePointerUp} />
<div class="overflow-x-auto rounded-lg">
	<table class="min-w-full text-sm">
		<thead>
			<tr class="border-b border-slate-200">
				<th class="sticky left-0 bg-white px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wide">Name</th>
				{#each sortedOptions as opt}
					{@const yesCount = countYes(opt.id)}
					{@const isBest = yesCount === bestCount && bestCount > 0}
					<th
						class="min-w-[70px] px-2 py-3 text-center
							{isBest ? 'bg-amber-50' : ''}"
					>
						{#if isBest}<div class="text-lg leading-none mb-0.5">{'\u{1F451}'}</div>{/if}
						<div class="text-[10px] font-semibold text-slate-400 uppercase">{format(parseISO(opt.date), 'EEE')}</div>
						<div class="text-sm font-semibold text-slate-700">{format(parseISO(opt.date), 'MMM d')}</div>
					</th>
				{/each}
			</tr>
		</thead>
		<tbody>
			{#each otherParticipants as p}
				<tr class="border-t border-slate-100 hover:bg-slate-50/50 transition-colors">
					<td class="sticky left-0 bg-white px-4 py-2.5 font-medium text-slate-800">{p.name}</td>
					{#each sortedOptions as opt}
						{@const v = p.votes.find((v) => v.date_option_id === opt.id)}
						{@const isBest = countYes(opt.id) === bestCount && bestCount > 0}
						<td class="px-2 py-2.5 text-center {isBest ? 'bg-amber-50/50' : ''}">
							{#if v}
								<span class="inline-flex h-7 w-7 items-center justify-center rounded-md text-xs font-bold {choiceColor(v.choice)}">
									{choiceIcon(v.choice)}
								</span>
							{:else}
								<span class="text-slate-200">&mdash;</span>
							{/if}
						</td>
					{/each}
				</tr>
			{/each}

			{#if editing}
				<tr class="border-t-2 border-blue-200 bg-blue-50/60">
					<td class="sticky left-0 bg-blue-50 px-4 py-2.5 font-semibold text-blue-700">{editingName || 'You'}</td>
					{#each sortedOptions as opt}
						{@const choice = editing.get(opt.id) ?? 'no'}
						<td class="px-2 py-2.5 text-center">
							<button
								type="button"
								class="inline-flex h-7 w-7 items-center justify-center cursor-pointer rounded-md text-xs font-bold touch-none select-none transition-all hover:scale-110 {choiceColor(choice)}"
								onpointerdown={(e) => handlePointerDown(opt.id, e)}
								onpointerenter={() => handlePointerEnter(opt.id)}
							>
								{choiceIcon(choice)}
							</button>
						</td>
					{/each}
				</tr>
			{/if}

			<!-- Summary row -->
			<tr class="border-t-2 border-slate-200">
				<td class="sticky left-0 bg-white px-4 py-2.5 text-xs font-semibold text-slate-500 uppercase tracking-wide">Total</td>
				{#each sortedOptions as opt}
					{@const yes = countYes(opt.id)}
					{@const maybe = countMaybe(opt.id)}
					{@const isBest = yes === bestCount && bestCount > 0}
					<td
						class="px-2 py-2.5 text-center font-bold
							{isBest ? 'bg-amber-50 text-amber-700' : 'text-slate-600'}"
					>
						<span class="text-base">{yes}</span>{#if maybe > 0}<span class="text-xs font-normal text-slate-400"> +{maybe}</span>{/if}
					</td>
				{/each}
			</tr>
		</tbody>
	</table>
</div>
