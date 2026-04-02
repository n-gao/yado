<script lang="ts">
	import {
		startOfMonth,
		endOfMonth,
		startOfWeek,
		endOfWeek,
		eachDayOfInterval,
		format,
		isSameMonth,
		addMonths,
		parseISO
	} from 'date-fns';
	import type { DateOption, Participant } from '$lib/api';

	type Choice = 'yes' | 'no' | 'maybe';

	interface Props {
		dateOptions: DateOption[];
		participants: Participant[];
		editing?: Map<string, Choice> | null;
		onSetVotes?: (updates: Map<string, Choice>) => void;
	}

	let { dateOptions, participants, editing = null, onSetVotes }: Props = $props();

	let optionByDate = $derived(new Map(dateOptions.map((o) => [o.date, o.id])));

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

	let bestCount = $derived(Math.max(0, ...dateOptions.map((o) => countYes(o.id))));

	let sortedDates = $derived([...dateOptions].sort((a, b) => a.date.localeCompare(b.date)));
	let initialMonth = $derived(
		sortedDates.length > 0 ? parseISO(sortedDates[0].date) : new Date()
	);

	let viewDate = $state<Date | null>(null);
	let effectiveView = $derived(viewDate ?? initialMonth);

	function toKey(d: Date): string {
		return format(d, 'yyyy-MM-dd');
	}

	function getCalendarDays(view: Date): Date[] {
		const monthStart = startOfMonth(view);
		const monthEnd = endOfMonth(view);
		const calStart = startOfWeek(monthStart, { weekStartsOn: 1 });
		const calEnd = endOfWeek(monthEnd, { weekStartsOn: 1 });
		return eachDayOfInterval({ start: calStart, end: calEnd });
	}

	let days = $derived(getCalendarDays(effectiveView));
	let monthLabel = $derived(format(effectiveView, 'MMMM yyyy'));

	const CYCLE: Choice[] = ['no', 'yes', 'maybe'];
	function nextChoice(c: Choice): Choice {
		return CYCLE[(CYCLE.indexOf(c) + 1) % CYCLE.length];
	}

	function choiceBg(choice: Choice): string {
		if (choice === 'yes') return 'bg-emerald-500 text-white';
		if (choice === 'maybe') return 'bg-amber-400 text-amber-900';
		return '';
	}

	let lastClicked: string | null = $state(null);
	let isDragging = $state(false);
	let dragChoice: Choice = $state('yes');

	function handlePointerDown(day: Date, e: PointerEvent) {
		if (!editing || !onSetVotes) return;
		const key = toKey(day);
		const optId = optionByDate.get(key);
		if (!optId) return;
		e.preventDefault();

		if (e.shiftKey && lastClicked) {
			const clickedOptId = optionByDate.get(key);
			if (!clickedOptId) return;
			const current = editing.get(clickedOptId) ?? 'no';
			const choice = nextChoice(current);
			const dA = new Date(lastClicked);
			const dB = day;
			const [start, end] = dA < dB ? [dA, dB] : [dB, dA];
			const range = eachDayOfInterval({ start, end });
			const updates = new Map<string, Choice>();
			for (const d of range) {
				const oid = optionByDate.get(toKey(d));
				if (oid) updates.set(oid, choice);
			}
			onSetVotes(updates);
		} else {
			const current = editing.get(optId) ?? 'no';
			dragChoice = nextChoice(current);
			onSetVotes(new Map([[optId, dragChoice]]));
			isDragging = true;
		}
		lastClicked = key;
	}

	function handlePointerEnter(day: Date) {
		if (!isDragging || !editing || !onSetVotes) return;
		const key = toKey(day);
		const optId = optionByDate.get(key);
		if (!optId) return;
		onSetVotes(new Map([[optId, dragChoice]]));
	}

	function handlePointerUp() {
		isDragging = false;
	}
</script>

<!-- svelte-ignore a11y_no_static_element_interactions -->
<svelte:window onpointerup={handlePointerUp} />
<div class="select-none">
	<!-- Legend -->
	<div class="mb-4 flex flex-wrap items-center gap-3 text-xs text-slate-500">
		{#if editing}
			<span class="flex items-center gap-1.5"><span class="inline-block h-3 w-3 rounded-sm bg-emerald-500"></span> Yes</span>
			<span class="flex items-center gap-1.5"><span class="inline-block h-3 w-3 rounded-sm bg-amber-400"></span> Maybe</span>
			<span class="flex items-center gap-1.5"><span class="inline-block h-3 w-3 rounded-sm border border-slate-300 bg-white"></span> No</span>
			<span class="text-slate-400">|</span>
			<span class="text-slate-400">Click, shift+click, or drag</span>
		{/if}
		{#if participants.length > 0}
			<span class="flex items-center gap-1">{'\u{1F451}'} Best date</span>
		{/if}
	</div>

	<!-- Month navigation -->
	<div class="mb-3 flex items-center justify-between">
		<button
			type="button"
			aria-label="Previous month"
			class="rounded-lg p-2 text-slate-600 hover:bg-slate-100 transition-colors"
			onclick={() => (viewDate = addMonths(effectiveView, -1))}>
			<svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M15.75 19.5L8.25 12l7.5-7.5" /></svg>
		</button>
		<span class="text-base font-semibold text-slate-800">{monthLabel}</span>
		<button
			type="button"
			aria-label="Next month"
			class="rounded-lg p-2 text-slate-600 hover:bg-slate-100 transition-colors"
			onclick={() => (viewDate = addMonths(effectiveView, 1))}>
			<svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" /></svg>
		</button>
	</div>

	<!-- Day headers -->
	<div class="grid grid-cols-7 gap-1.5 text-center text-xs font-semibold text-slate-400 uppercase tracking-wide mb-1">
		{#each ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'] as d}
			<div class="py-1">{d}</div>
		{/each}
	</div>

	<!-- Day grid -->
	<div class="grid grid-cols-7 gap-2">
		{#each days as day}
			{@const key = toKey(day)}
			{@const inMonth = isSameMonth(day, effectiveView)}
			{@const optId = optionByDate.get(key)}
			{@const isOption = !!optId}
			{@const choice = editing && optId ? (editing.get(optId) ?? 'no') : 'no'}
			{@const yes = optId ? countYes(optId) : 0}
			{@const maybe = optId ? countMaybe(optId) : 0}
			{@const isBest = isOption && bestCount > 0 && yes === bestCount}
			<button
				type="button"
				disabled={!isOption || !editing}
				class="relative flex flex-col items-center justify-center rounded-lg text-sm font-medium transition-all touch-none aspect-square
					{!isOption ? 'cursor-default text-slate-200' : ''}
					{isOption && !editing ? 'cursor-default' : ''}
					{isOption && editing ? 'cursor-pointer' : ''}
					{!inMonth && !isOption ? 'text-slate-200' : ''}
					{isOption && editing ? choiceBg(choice) || 'bg-white text-slate-700 hover:bg-slate-100 ring-1 ring-inset ring-slate-200' : ''}
					{isOption && !editing ? 'bg-white text-slate-700 ring-1 ring-inset ring-slate-200' : ''}
					{isBest ? 'ring-[3px] ring-amber-400 shadow-md shadow-amber-200/50' : ''}"
				onpointerdown={(e) => handlePointerDown(day, e)}
				onpointerenter={() => handlePointerEnter(day)}
			>
				{#if isBest}
					<span class="absolute -top-2.5 left-1/2 -translate-x-1/2 text-base drop-shadow-sm">{'\u{1F451}'}</span>
				{/if}
				<span class="leading-tight">{format(day, 'd')}</span>
				{#if isOption && participants.length > 0}
					<span class="text-[10px] leading-none font-semibold {isBest && !editing ? 'text-amber-600' : ''} {editing ? (choice === 'no' ? 'text-slate-400' : 'opacity-80') : 'text-slate-400'}">
						{yes}{maybe > 0 ? `+${maybe}` : ''}
					</span>
				{/if}
			</button>
		{/each}
	</div>
</div>
