COMPLETE: Add built in recession shading, applied to charts by default. Make it possible to disable it through passing an optional boolean argument. Test that shading is aligned to the time axis and that it will be dynamically adjusted if the axis changes. Update the examples and tests to reflect this.

Make it unnecessary to pass HTML tags for plotly titles. Have users pass the heading level (1 corresponds to <h1>, 2 to <h2> etc.) as an optional argument. Default to 1 (<h1>) if no argument is passed. 

COMPLETE: Split EconChart into Subplot and EconChart classes. EconChart should be a collection of subplots that display together.

Include instance variables in EconBase
