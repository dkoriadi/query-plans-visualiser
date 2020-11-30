"""
app.py

Entry point of the query-plan-visualizer application.

This app allows several possible query execution plans (QEPs) to be displayed for a given a query, 
and compare between the QEPs. 

Tested successfully on the following environments:
- Python 3.7.9
- PostgreSQL 9.6.X with TPC-H dataset 

Dependencies:
- anytree (2.8.0) - For visualising the QEP
- jsondiff (1.2.0) - For parsing QEPs given by PostgreSQL database server
- psycopg2 (2.8.6) - For communicating with PostgreSQL database server
- sqlparse (0.4.1) - For parsing the input SQL query

"""
import tkinter
from tkinter import messagebox

# Create the Tkinter frames to be placed inside the Tkinter window in QueryTool() class
import MainFrame
import PlansFrame


class QueryTool(tkinter.Toplevel):
    """
    This is the class that launches the two Tkinter frames - LandingPage (input query) and PlansPage (view plans)

    Attributes
    ----------

    dictFramePage : dict
        Key: The class (LandingPage/PlansPage) which inherits the Tkinter Frame class
        Value: The object instantiated from the class above
        Used to switch between the LandingPage and the PlansPage. When the class name is passed as an argument, 
        the actual object will be referred to. 

    Methods
    -------
    showFrame(pageName)
        Switches between the LandingPage and PlansPage upon clicking button

    getPage(className)
        Returns an instance of a page given its class name as a string

    """

    def __init__(self, root):
        """
        Create two Tkinter frames within this Tkinter window:
        - MainFrame.LandingPage : Tkinter frame which contains the SQL query input and explanation
        - PlansFrame.PlansPage: Tkinter frame which contains all possible QEPs

        Switching between frames is handled by the showFrame() function within this class

        """

        # Always initialise Tkinter window first
        tkinter.Toplevel.__init__(self, root)

        """ Initialise UI """
        container = tkinter.Frame(self)
        # The fill option tells the grid manager that the widget wants to fill the entire space assigned to it.
        # The value controls how to fill the space; "both" means that the widget should expand both
        # horizontally and vertically.
        # The expand option tells the grid manager to fill up remaining space available when window is
        # maximised.
        container.pack(fill="both", expand=True)

        # To fill up entire screen when Tkinter window is expanded
        # Weight determines distribution of additional space between rows.
        # "0" is the row index of the container.
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        # Create empty dictionary
        self.dictFramePage = {}

        tk_parent_frame = container
        tk_root_window = self

        # Constuctor for both pages to be stored into the frames dictionary
        # More info about the arguments shown here can be found in the __init__ function of the
        # respective classes
        objLandingPage = MainFrame.LandingPage(tk_parent_frame, tk_root_window)
        objPlansPage = PlansFrame.PlansPage(
            tk_parent_frame, tk_root_window, objLandingPage=objLandingPage)
        # Insert the object instantiated into the frames dictionary
        self.dictFramePage[MainFrame.LandingPage] = objLandingPage
        self.dictFramePage[PlansFrame.PlansPage] = objPlansPage

        # Put all of the pages in the same row and column. The one on top of the
        # stacking order will be the one that is visible.
        # "sticky" determines where the frame is filled when expanded
        objLandingPage.grid(row=0, column=0, sticky="nsew")
        # "nsew" means to fill up entire window
        objPlansPage.grid(row=0, column=0, sticky="nsew")

        self.showFrame(MainFrame.LandingPage)

    def showFrame(self, className):
        """
        Shows the frame given selected via the dictionary 

        Parameters
        ---------- 
        className: Name of the page to be shown

        """

        frame = self.dictFramePage[className]
        frame.tkraise()

    def getPage(self, className):
        """
        Returns an instance of a page given its class name as a string

        Parameters
        ---------- 
        className: The class of the frame i.e. either "LandingPage" or "PlansPage"
                   only

        Returns
        ------- 
        pageObj: The instance of the page if the input is valid
                 Else, NoneType is returned

        """
        for pageObj in self.dictFramePage.values():
            if str(pageObj.__class__.__name__) == className:
                return pageObj
        return None


def main():

    def _onCloseWindow():
        """
        To create a pop asking for confirmation before closing the window

        """

        if tkinter.messagebox.askokcancel("Quit", "Do you want to quit?"):
            root.quit()  # stops mainloop

    root = tkinter.Tk()
    root.withdraw()  # Hide the root so that only the popups will be visible

    app = QueryTool(root)
    # .geometry("window width x window height + position right + position down")
    app.geometry("1100x680+200+50")
    # Title to be displayed on window
    app.title('Query Plans Visualizer')
    # Callback for user pressing the "X" button, otherwise window closes without confirmation
    app.protocol("WM_DELETE_WINDOW", _onCloseWindow)
    # mainloop() keeps the Tkinter frame alive
    root.mainloop()


if __name__ == "__main__":
    main()
