# Nonograms
An apparently-very-simple-but-then-appears-to-be-quite-challenging-and-time-consuming-to-make static puzzle game made with fundamental python concepts and basic pygame 2.0.1 - no sprites!.

## Version 1.0.0 
### Note (also note to self lol)
If you wish to add an additional page from the start menu, add it as a method (currently with no extra arguments) in `kwindows.KWindow` class.

Here is an example of a minimally functional page

```
# kwindows.py

class KWindow():
    ...
    def new_page(self) -> str:
        self.screen.fill(self.color_bgdf)
        back_button = KButton(
            self.screen,
            "Back",
            50,
            (100, 50),
            (25, 25),
            KColor.name('white'),
            KColor.name('black'),
            on_pressed = lambda: "start_menu",
            on_released = None,
        )
        button.draw()
        target_page = str()
        while not target_page:
            self.clock.tick(self.fps)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    target_page = "exit_prompt"
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    _mpos = pygame.mouse.get_pos()
                    clicked, target_page = back_button.check(_mpos)
                    if clicked:
                        continue
            pygame.display.flip()
        if target_page == "exit_prompt":
            KWindow._PREVPAGE = "new_page"
        return target_page

```

Then, similarly add a button in the start_menu() method, be sure to use the **exact** name of the method to set the flag. 

```
button_to_page = KButton(..., on_pressed = lambda: "new_page")
```