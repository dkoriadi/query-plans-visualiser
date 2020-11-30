"""
PlansFrame.py

This script is called by app.py to display multiple QEPs in tree format.

"""

import tkinter
import tkinter.scrolledtext

import MainFrame


class PlansPage(tkinter.Frame):
    """
    This is the class that displays the plans page whereto view all possible QEPs. It is displayed as a 
    separate frame from the landing page. The QEPs may also be viewed on the CLI for convienience.

    Methods
    -------
    displayPlans(planStrings)
        Display all possible QEPs and actual QEP on GUI and CLI

    """

    def onFrameConfigure(self, event):
        """
        Update the scrollregion of the canvas to allow scrolling on the scrollbar

        Parameters
        ---------- 
        event: Tkinter event (in this case, left-click)  

        """
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def displayPlans(self, planStrings):
        # Display QEPs on GUI
        self.label_plans.configure(state='normal')
        # Remove previous plans
        self.label_plans.delete('1.0', tkinter.END)
        self.label_plans.insert('end', planStrings + '\n')
        self.label_plans.configure(state='disabled')

    def __init__(self, tk_parent_frame, tk_root_window, objLandingPage):
        """
        Constructor of the PlansPage class

        Parameters
        ---------- 
        tk_parent_frame: tkinter.Frame
            The parent Tkinter frame that is on top of the Tkinter window. Every Tkinter window must contain 
            a widget (the frame in this case) to be able to display UI.

        tk_root_window: tkinter.Tk
            The Tkinter root window which has one or more Tkinter frames created as objects. Switching the 
            Tkinter frame is done via the root window.

        """

        tkinter.Frame.__init__(self, tk_parent_frame, width=300, height=300)
        self.controller = tk_root_window
        self.canvas = tkinter.Canvas(self, width=300, height=300)
        self.canvas.pack(side=tkinter.LEFT, expand=True, fill=tkinter.BOTH)
        self.frame = tkinter.Frame(self.canvas)

        # Get the LandingPage object to pass variables
        self.objLandingPage = objLandingPage

        # Vertical scrollbar
        self.yscroll = tkinter.Scrollbar(
            self, command=self.canvas.yview, orient=tkinter.VERTICAL)
        self.yscroll.pack(side=tkinter.RIGHT, fill=tkinter.Y,
                          expand=tkinter.FALSE)
        self.canvas.configure(yscrollcommand=self.yscroll.set)
        self.canvas.create_window((0, 0), window=self.frame, anchor="nw",
                                  tags="self.frame")

        # Horizontal scrollbar
        self.xscroll = tkinter.Scrollbar(
            self.canvas, orient='horizontal', command=self.canvas.xview)
        self.xscroll.pack(side=tkinter.BOTTOM, fill=tkinter.X)
        # Callback function for scrollbar
        self.frame.bind("<Configure>", self.onFrameConfigure)

        # Button created to allow user to go back to LandingPage
        tkinter.Button(
            self.frame, text="Back",
            command=lambda: self.controller.showFrame(MainFrame.LandingPage)).grid(row=0, column=0, padx=(10, 0), pady=9)

        """Plans"""
        self.label_plans_header = tkinter.Label(
            self.canvas, text="Plans:", anchor="w")
        self.label_plans_header.config(font=(None, 14))
        self.label_plans_header.pack(padx=(10, 0), pady=(15, 0))
        self.label_plans = tkinter.scrolledtext.ScrolledText(
            self.canvas, wrap='word', state='disabled', width=130, height=100)
        self.label_plans.pack(padx=(10, 10), pady=(10, 10))
