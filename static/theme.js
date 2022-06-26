$().ready(function() {
	if (localStorage.theme === 'dark' || (!('theme' in localStorage) && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
		document.documentElement.classList.add('dark')
		localStorage.setItem('theme', 'dark')
		$("#light-icon").hide();
		// console.log('0');
	} else {
		document.documentElement.classList.remove('dark')
		localStorage.setItem('theme', 'light')
		$("#dark-icon").hide();
		// console.log('1');
	}

	$("#theme-toggle").click(function() {
		if (localStorage.getItem('theme') == 'dark') {
			document.documentElement.classList.remove('dark')
			localStorage.setItem('theme', 'light')
			$("#dark-icon").hide();
			$("#light-icon").show();
		} else {
			document.documentElement.classList.add('dark')
			localStorage.setItem('theme', 'dark')
			$("#light-icon").hide();
			$("#dark-icon").show();
		}
	});
});
