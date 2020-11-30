"""
MainFrame.py

This script is called by app.py to display the landing page.

"""
# GUI modules
import tkinter

import db_connection_manager as db_connect
import qep_processor
import query_plan_visualizer as visualiser

import PlansFrame


class LandingPage(tkinter.Frame):
    """
    This is the class that allows user to input query and display explanation and generate QEPs.

    Methods
    -------

    onExplainQuery()
        Callback function when "Explain Query" is clicked on.
        Connects to PostgreSQL database based on database information entered on the GUI, then
        generates explanation and QEPs to display.

    """

    def onFrameConfigure(self, event):
        """
        Update the scrollregion of the canvas to allow scrolling on the scrollbar

        Parameters
        ---------- 
        event: Tkinter event (in this case, left-click)  

        """
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def onEnterDatabaseInfo(self, event, info):
        """
        Callback function to detect when left click happens on entry boxes.
        This removes default text in the box.

        Parameters
        ---------- 
        event : Tkinter event (in this case, left-click)  

        info: To determine which entry box was clicked 

        """
        if info == "database_name":
            if self.entryDatabaseName.get() == 'TPC-H':
                # delete all the text in the entry
                self.entryDatabaseName.delete(0, "end")
                self.entryDatabaseName.insert(
                    0, '')  # Insert blank for user input
        elif info == "user":
            if self.entryUser.get() == 'postgres':
                # delete all the text in the entry
                self.entryUser.delete(0, "end")
                self.entryUser.insert(
                    0, '')  # Insert blank for user input
        elif info == "password":
            if self.entryPassword.get() == 'root':
                # Delete all the text in the entry
                self.entryPassword.delete(0, "end")
                self.entryPassword.insert(
                    0, '')  # Insert blank for user input
        elif info == "host":
            if self.entryHost.get() == 'localhost':
                # Delete all the text in the entry
                self.entryHost.delete(0, "end")
                self.entryHost.insert(
                    0, '')  # Insert blank for user input
        elif info == "port":
            if self.entryPort.get() == '5432':
                # Delete all the text in the entry
                self.entryPort.delete(0, "end")
                self.entryPort.insert(
                    0, '')  # Insert blank for user input

    def onExplainQuery(self):
        """
        Callback function when "Explain Query" is clicked on.
        Connects to PostgreSQL database based on database information entered on the GUI, then
        generates explanation and QEPs to display.

        """
        Communicator = self.connectDatabase()

        # Check if query box is empty first
        if len(self.entry_query.get("1.0", "end-1c")) == 0:
            print("Empty query")
            tkinter.messagebox.showwarning(
                title="Empty query", message="No query has been entered. Please enter a query")
            return

        query = self.entry_query.get("1.0", "end-1c")
        self.plan_trees = ""
        lstAllQEPs = None
        lstPredicateAttributes = None
        selectivityMap = None
        result = qep_processor.processQuery(
            query, Communicator)
        if result[0] == qep_processor.RET_CONVERT_QUERY_ERR:
            szErrorMessage = "Error parsing query for predicates! Running actual query...\nView the actual QEP in the Plans page\n"
            res = qep_processor.getActualQEP(query, Communicator)
            szQEPTree = visualiser.visualize_query_plan(res[1])
            self.plan_trees += szQEPTree
            print(szErrorMessage)
            print(szQEPTree)
            self.displayExplanation(szErrorMessage)
            return
        elif result[0] == qep_processor.RET_ALL_QEPS:
            lstAllQEPs = result[1]
            lstPredicateAttributes = result[2]
            selectivityMap = result[3]

        explanationString = "Number of QEPs found: {}\n".format(
            len(lstAllQEPs))
        self.plan_trees = explanationString
        string = str()
        # Show the QEPs found. It is displayed as a normal Python string
        print("\nNumber of QEPs found: {}".format(len(lstAllQEPs)))
        for index, plan in enumerate(lstAllQEPs):
            string = ("Plan {}:\n\n".format(index+1))
            print("Plan {}:".format(index+1))
            print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
            szQEPTree = visualiser.visualize_query_plan(plan)
            self.plan_trees += string + szQEPTree
            print(szQEPTree)
            print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@\n")

        result = qep_processor.getActualQEP(query, Communicator)
        if result[0] == qep_processor.RET_ONLY_ACTUAL_QEP:
            # Retrieve actual QEP
            actualQEP = result[1]
            szQEPTree = visualiser.visualize_query_plan(actualQEP)
            string = "Actual plan:\n"
            print(string + szQEPTree)
            self.plan_trees += string + szQEPTree
            # Compare actual QEP with predicted QEP
            result = qep_processor.compareActualQEP(actualQEP, lstAllQEPs)
            if result[0] == qep_processor.RET_QEP_FOUND:
                lstSelectivityExplanations = qep_processor.generateFoundExplanation(
                    lstPredicateAttributes, selectivityMap)
                for string in lstSelectivityExplanations:
                    explanationString += string
                string = ("The selectivity range of the query is closest to Plan {}.\n".format(
                    result[1]))
                explanationString += string
                self.plan_trees += "\n" + string
            elif result[0] == qep_processor.RET_QEP_NOT_FOUND:
                string = (
                    """A different plan is seen because the DBMS may have considered other plans with different selectivity values 
                    which result in lower cost for the plan. 
                    """)
                explanationString += string

        self.displayExplanation(explanationString)

    def displayExplanation(self, explanationString):
        """
        Display explanation on GUI on this frame, and also displays the plan trees 
        on the PlansPage at the same time

        Parameters
        ---------- 
        explanationString : String 
            This parameter includes the text to display on the LandingPage  

        """
        # Display explanation on GUI
        self.label_explanation.configure(state='normal')
        # Remove previous explanations
        self.label_explanation.delete('1.0', tkinter.END)
        self.label_explanation.insert('end', explanationString + '\n')
        self.label_explanation.configure(state='disabled')

        objPlansPage = self.tk_root_window.getPage("PlansPage")
        objPlansPage.displayPlans(self.plan_trees)

    def connectDatabase(self):
        """
        Connect to PostgreSQL database

        """
        host = self.entryHost.get()
        port = self.entryPort.get()
        database = self.entryDatabaseName.get()
        username = self.entryUser.get()
        password = self.entryPassword.get()

        # Build Connections to the Server
        Communicator = db_connect.Postgres_Connect()
        Communicator.connect(host, database, port, username, password)
        return Communicator

    def __init__(self, tk_parent_frame, tk_root_window):
        """
        Constructor of the LandingPage class

        Parameters
        ---------- 
        tk_parent_frame: tkinter.Frame
            The parent Tkinter frame that is on top of the Tkinter window. Every Tkinter window must contain 
            a widget (the frame in this case) to be able to display UI.

        tk_root_window: tkinter.Tk
            The Tkinter root window which has one or more Tkinter frames created as objects. Switching the 
            Tkinter frame is done via the root window.

        """

        tkinter.Frame.__init__(self, tk_parent_frame)
        self.tk_root_window = tk_root_window
        self.canvas = tkinter.Canvas(self, width=300, height=300)
        self.canvas.pack(side=tkinter.LEFT, expand=True, fill=tkinter.BOTH)
        self.frame = tkinter.Frame(self.canvas)

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

        # Create frame above the graph window to enter database details
        self.frameDatabaseInput = tkinter.Frame(self.frame)
        # Change anchor to decide where the widgets should lean towards
        self.frameDatabaseInput.pack(
            side=tkinter.TOP, anchor="center", expand=False)

        # Display plans button which brings user to the second page in PlansPage class
        # Command within button cant throw args to funcs. Use lambda to throw those args to the func instead
        tkinter.Button(
            self.frameDatabaseInput,
            text="View Plans",
            background="black",
            foreground="white",
            command=lambda: self.tk_root_window.showFrame(PlansFrame.PlansPage)).grid(
            row=1, column=4, columnspan=2, pady=5, padx=5, sticky="nsew")

        """Database details"""
        # Database name
        tkinter.Label(self.frameDatabaseInput, text="Database Name:").grid(
            row=0, column=0, sticky="ew", pady=(12, 0))
        self.entryDatabaseName = tkinter.Entry(
            self.frameDatabaseInput, width=20, justify=tkinter.LEFT)
        self.entryDatabaseName.grid(
            row=0, column=1, padx=(5, 10), pady=(20, 5))
        self.entryDatabaseName.insert(0, "TPC-H")
        self.entryDatabaseName.bind(
            '<FocusIn>', lambda event: self.onEnterDatabaseInfo(event, "database_name"))
        # User
        tkinter.Label(self.frameDatabaseInput, text="User:").grid(
            row=0, column=2, sticky="ew", pady=(12, 0))
        self.entryUser = tkinter.Entry(
            self.frameDatabaseInput, width=20, justify=tkinter.LEFT)
        self.entryUser.grid(
            row=0, column=3, padx=(5, 10), pady=(20, 5))
        self.entryUser.insert(0, "postgres")
        self.entryUser.bind(
            '<FocusIn>', lambda event: self.onEnterDatabaseInfo(event, "user"))
        # Password
        tkinter.Label(self.frameDatabaseInput, text="Password:").grid(
            row=0, column=4, sticky="ew", pady=(12, 0))
        self.entryPassword = tkinter.Entry(
            self.frameDatabaseInput, width=20, justify=tkinter.LEFT)
        self.entryPassword.grid(
            row=0, column=5, padx=(5, 10), pady=(20, 5))
        self.entryPassword.insert(0, "root")
        self.entryPassword.bind(
            '<FocusIn>', lambda event: self.onEnterDatabaseInfo(event, "password"))
        # Host
        tkinter.Label(self.frameDatabaseInput, text="Host:").grid(
            row=0, column=6, sticky="ew", pady=(12, 0))
        self.entryHost = tkinter.Entry(
            self.frameDatabaseInput, width=20, justify=tkinter.LEFT)
        self.entryHost.grid(
            row=0, column=7, padx=(5, 10), pady=(20, 5))
        self.entryHost.insert(0, "localhost")
        self.entryHost.bind(
            '<FocusIn>', lambda event: self.onEnterDatabaseInfo(event, "host"))
        # Port number
        tkinter.Label(self.frameDatabaseInput, text="Port Number:").grid(
            row=0, column=8, sticky="ew", pady=(12, 0))
        self.entryPort = tkinter.Entry(
            self.frameDatabaseInput, width=20, justify=tkinter.LEFT)
        self.entryPort.grid(
            row=0, column=9, padx=(5, 10), pady=(20, 5))
        self.entryPort.insert(0, "5432")
        self.entryPort.bind(
            '<FocusIn>', lambda event: self.onEnterDatabaseInfo(event, "port"))

        """Query input"""
        # Create frame to enter query and show explanation
        self.frameQueryInput = tkinter.Frame(self.frame)
        # Change anchor to decide where the widgets should lean towards
        self.frameQueryInput.pack(
            side=tkinter.BOTTOM, anchor="w", expand=False)
        self.label_query = tkinter.Label(
            self.frameQueryInput, text="Query:", anchor="w")
        self.label_query.config(font=(None, 15))
        self.label_query.grid(column=0, row=5, columnspan=1,
                              sticky='W', padx=(10, 0))
        self.frame_query = tkinter.Frame(self.frameQueryInput)
        self.frame_query.grid(
            column=0, row=6, columnspan=6, rowspan=1, sticky='W')

        self.button_query_text = tkinter.StringVar()
        self.button_query = tkinter.Button(
            self.frame_query,
            background="black", textvariable=self.button_query_text,
            foreground="white",
            width=25, command=self.onExplainQuery)
        self.button_query_text.set("Explain Query")
        self.button_query.pack(side=tkinter.BOTTOM, pady=(5, 5))
        self.entry_query = tkinter.Text(
            self.frame_query, height=15, width=120, wrap=tkinter.WORD)
        self.entry_query.pack(side='left', fill='both',
                              expand=True, padx=(10, 0))
        self.scrollbar_query = tkinter.Scrollbar(self.frame_query)
        self.entry_query.config(yscrollcommand=self.scrollbar_query.set)
        self.scrollbar_query.config(command=self.entry_query.yview)
        self.grid()
        self.scrollbar_query.pack(side='right', fill='y')

        """Explanation"""
        self.label_explain_header = tkinter.Label(
            self.frameQueryInput, text="Explanation:", anchor="w")
        self.label_explain_header.config(font=(None, 14))
        self.label_explain_header.grid(
            column=0, row=10, columnspan=1, sticky='W', padx=(10, 0))
        self.label_explanation = tkinter.Text(self.frameQueryInput, wrap='word', state='disabled', width=108, height=12,
                                              font=("Arial", 12))
        self.label_explanation.grid(
            column=0, row=11, columnspan=2, sticky='w', padx=(10, 10), pady=(10, 10))
