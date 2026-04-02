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
		isBefore,
		startOfDay,
		addDays,
		isWeekend
	} from 'date-fns';

	interface Props {
		selected: Set<string>;
		onchange: (dates: Set<string>) => void;
	}

	let { selected, onchange }: Props = $props();

	const today = startOfDay(new Date());
	let viewDate = $state(new Date());
	let lastClicked: string | null = $state(null);
	let isDragging = $state(false);
	let dragValue = $state(true);

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

	let days = $derived(getCalendarDays(viewDate));
	let monthLabel = $derived(format(viewDate, 'MMMM yyyy'));

	function toggle(key: string, value: boolean) {
		const next = new Set(selected);
		if (value) next.add(key);
		else next.delete(key);
		onchange(next);
	}

	function rangeBetween(a: string, b: string): string[] {
		const dA = new Date(a);
		const dB = new Date(b);
		const [start, end] = dA < dB ? [dA, dB] : [dB, dA];
		return eachDayOfInterval({ start, end }).map(toKey);
	}

	function handlePointerDown(day: Date, e: PointerEvent) {
		if (isBefore(day, today)) return;
		e.preventDefault();
		const key = toKey(day);

		if (e.shiftKey && lastClicked) {
			const keys = rangeBetween(lastClicked, key);
			const next = new Set(selected);
			const adding = !selected.has(key);
			for (const k of keys) {
				if (adding) next.add(k);
				else next.delete(k);
			}
			onchange(next);
		} else {
			dragValue = !selected.has(key);
			toggle(key, dragValue);
		}

		isDragging = true;
		lastClicked = key;
	}

	function handlePointerEnter(day: Date) {
		if (!isDragging) return;
		if (isBefore(day, today)) return;
		const key = toKey(day);
		toggle(key, dragValue);
	}

	function handlePointerUp() {
		isDragging = false;
	}

	function quickFill(numDays: number, weekdaysOnly: boolean) {
		const next = new Set(selected);
		let d = today;
		let added = 0;
		while (added < numDays) {
			if (!weekdaysOnly || !isWeekend(d)) {
				next.add(toKey(d));
				added++;
			}
			d = addDays(d, 1);
		}
		onchange(next);
	}

	function clearAll() {
		onchange(new Set());
	}
</script>

<!-- svelte-ignore a11y_no_static_element_interactions -->
<svelte:window onpointerup={handlePointerUp} />
<div class="select-none">
	<!-- Quick fill buttons -->
	<div class="mb-4 flex flex-wrap gap-2">
		<button
			type="button"
			class="rounded-lg border border-blue-200 bg-blue-50 px-3 py-1.5 text-sm font-medium text-blue-700 hover:bg-blue-100 transition-colors"
			onclick={() => quickFill(7, false)}>Next 7 days</button
		>
		<button
			type="button"
			class="rounded-lg border border-blue-200 bg-blue-50 px-3 py-1.5 text-sm font-medium text-blue-700 hover:bg-blue-100 transition-colors"
			onclick={() => quickFill(30, false)}>Next 30 days</button
		>
		<button
			type="button"
			class="rounded-lg border border-blue-200 bg-blue-50 px-3 py-1.5 text-sm font-medium text-blue-700 hover:bg-blue-100 transition-colors"
			onclick={() => quickFill(30, true)}>Weekdays (30d)</button
		>
		{#if selected.size > 0}
			<button
				type="button"
				class="rounded-lg border border-red-200 bg-red-50 px-3 py-1.5 text-sm font-medium text-red-600 hover:bg-red-100 transition-colors"
				onclick={clearAll}>Clear</button
			>
		{/if}
	</div>

	<!-- Month navigation -->
	<div class="mb-3 flex items-center justify-between">
		<button
			type="button"
			aria-label="Previous month"
			class="rounded-lg p-2 text-slate-600 hover:bg-slate-100 transition-colors"
			onclick={() => (viewDate = addMonths(viewDate, -1))}>
			<svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M15.75 19.5L8.25 12l7.5-7.5" /></svg>
		</button>
		<span class="text-base font-semibold text-slate-800">{monthLabel}</span>
		<button
			type="button"
			aria-label="Next month"
			class="rounded-lg p-2 text-slate-600 hover:bg-slate-100 transition-colors"
			onclick={() => (viewDate = addMonths(viewDate, 1))}>
			<svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" /></svg>
		</button>
	</div>

	<!-- Day headers -->
	<div class="grid grid-cols-7 gap-1 text-center text-xs font-semibold text-slate-400 uppercase tracking-wide mb-1">
		{#each ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'] as d}
			<div class="py-1">{d}</div>
		{/each}
	</div>

	<!-- Day grid -->
	<div class="grid grid-cols-7 gap-1">
		{#each days as day}
			{@const key = toKey(day)}
			{@const inMonth = isSameMonth(day, viewDate)}
			{@const past = isBefore(day, today)}
			{@const isSelected = selected.has(key)}
			<button
				type="button"
				disabled={past}
				class="aspect-square rounded-lg text-sm font-medium transition-all touch-none
					{past ? 'cursor-default text-slate-200' : 'cursor-pointer'}
					{!inMonth && !past ? 'text-slate-300' : ''}
					{isSelected ? 'bg-blue-600 text-white shadow-sm scale-105' : ''}
					{!isSelected && !past ? 'hover:bg-slate-100 text-slate-700' : ''}"
				onpointerdown={(e) => handlePointerDown(day, e)}
				onpointerenter={() => handlePointerEnter(day)}
			>
				{format(day, 'd')}
			</button>
		{/each}
	</div>

	{#if selected.size > 0}
		<p class="mt-3 text-sm font-medium text-slate-500">{selected.size} date{selected.size === 1 ? '' : 's'} selected</p>
	{/if}
</div>
