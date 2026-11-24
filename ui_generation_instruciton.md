Act as an Expert UI/UX Designer and Frontend Developer specializing in Tailwind CSS. I am building a "History Timeline" web app using Django. 

The app allows history and literature students to log in, add historical events, and view them on an interactive horizontal timeline (using Vis.js or TimelineJS). 

I need you to design the User Interface and provide the HTML/Tailwind CSS code for my Django templates. Do NOT write React/Next.js code; provide standard HTML with Tailwind classes that I can drop directly into Django.

**Here are the specific UX challenges and requirements:
**1. Theme & Vibe: The app should feel academic, clean, and modern, but with subtle historical nods (e.g., a warm, paper-like background color palette, elegant typography pairing serif for headings and clean sans-serif for UI elements).
2. The "Date Input" Challenge: Standard date pickers break for ancient and BCE dates. The database uses Integers for Year, Month, and Day. The UI needs a clever, user-friendly form to handle this (e.g., number inputs with a toggle for "CE / BCE").
3. The Dashboard Layout: The timeline will be the star of the show, taking up most of the screen. Users need a sidebar or top navigation to filter by tags (e.g., #BanglaLiterature, #WorldWar, #BCE).

Please generate a comprehensive UI/UX design guide and code, including:

1. Color Palette & Typography: Recommend specific Tailwind color utility classes (e.g., slate-800, amber-50) and Google Fonts that fit the historical/academic theme.
2. Layout Strategy (Wireframe Description): Explain the layout of the Main Dashboard. Where does the timeline go? Where do the filters go? How does a user open the "Add Event" form?
3. Code Deliverable 1 - The Main Dashboard: Write the HTML/Tailwind CSS boilerplate for the main dashboard view. Include a placeholder `<div>` where the JS Timeline will render, a sidebar for categories/tags, and a top navigation bar with a "New Event" button.
4. Code Deliverable 2 - The Event Creation Modal/Form: Write the HTML/Tailwind CSS for the form where users add events. Focus heavily on making the custom integer-based date input (Year, Month, Day, BCE toggle) look intuitive and beautiful without relying on the native browser `<input type="date">`.

Please ensure all code is responsive (mobile-friendly) and uses standard Tailwind CSS classes.
