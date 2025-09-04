#!/usr/bin/env python3
"""
Llama Herder - GUI Application
A comprehensive tool for managing Ollama models on your local system.
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import requests
import subprocess
import threading
import json
import os
import time
from datetime import datetime
import webbrowser

class OllamaManager:
    def __init__(self, root):
        self.root = root
        self.root.title("Llama Herder")
        self.root.geometry("1000x700")
        self.root.minsize(800, 600)
        
        # Configure style
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Ollama API base URL
        self.ollama_url = "http://localhost:11434"
        
        # Available models data (will be populated from web)
        self.available_models = {}
        
        # Create GUI
        self.create_widgets()
        
        # Download tracking
        self.download_active = False
        self.current_download_model = None
        
        # Load initial data
        self.refresh_installed_models()
        self.load_available_models()
    
    def create_widgets(self):
        """Create the main GUI layout"""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="Llama Herder", 
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Left panel - Installed Models
        self.create_installed_models_panel(main_frame)
        
        # Right panel - Available Models
        self.create_available_models_panel(main_frame)
        
        # Download status area (initially hidden)
        self.download_status_frame = ttk.LabelFrame(main_frame, text="Download Status", padding="5")
        self.download_status_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
        self.download_status_frame.columnconfigure(0, weight=1)
        self.download_status_frame.grid_remove()  # Hide initially
        
        # Download status text
        self.download_status_var = tk.StringVar()
        self.download_status_var.set("")
        download_status_label = ttk.Label(self.download_status_frame, textvariable=self.download_status_var, 
                                        font=('Arial', 10, 'bold'), foreground='blue')
        download_status_label.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self.download_status_frame, variable=self.progress_var, 
                                          maximum=100, length=300)
        self.progress_bar.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(5, 0))
        
        # Progress details
        self.progress_label_var = tk.StringVar()
        self.progress_label = ttk.Label(self.download_status_frame, textvariable=self.progress_label_var,
                                       font=('Arial', 9))
        self.progress_label.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(2, 0))
        
        # Button frame for download controls
        download_btn_frame = ttk.Frame(self.download_status_frame)
        download_btn_frame.grid(row=3, column=0, pady=(5, 0))
        download_btn_frame.columnconfigure(0, weight=1)
        download_btn_frame.columnconfigure(1, weight=1)
        
        # Cancel button (initially hidden)
        self.cancel_download_btn = ttk.Button(download_btn_frame, text="Cancel Download",
                                            command=self.cancel_download)
        self.cancel_download_btn.grid(row=0, column=0, padx=(0, 5), sticky=(tk.W, tk.E))
        self.cancel_download_btn.grid_remove()  # Hide initially
        
        # Resume button (initially hidden)
        self.resume_download_btn = ttk.Button(download_btn_frame, text="Resume Download",
                                            command=self.resume_download)
        self.resume_download_btn.grid(row=0, column=1, padx=(5, 0), sticky=(tk.W, tk.E))
        self.resume_download_btn.grid_remove()  # Hide initially
        
        # Main status bar
        status_frame = ttk.Frame(main_frame)
        status_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(5, 0))
        status_frame.columnconfigure(0, weight=1)
        
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_bar = ttk.Label(status_frame, textvariable=self.status_var, 
                              relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=0, column=0, sticky=(tk.W, tk.E))
    
    def create_installed_models_panel(self, parent):
        """Create the installed models panel"""
        # Installed models frame
        installed_frame = ttk.LabelFrame(parent, text="Installed Models", padding="10")
        installed_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        installed_frame.columnconfigure(0, weight=1)
        installed_frame.rowconfigure(1, weight=1)
        
        # Refresh button
        refresh_btn = ttk.Button(installed_frame, text="Refresh", 
                                command=self.refresh_installed_models)
        refresh_btn.grid(row=0, column=0, pady=(0, 10))
        
        # Installed models listbox
        list_frame = ttk.Frame(installed_frame)
        list_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        
        self.installed_listbox = tk.Listbox(list_frame, selectmode=tk.SINGLE)
        scrollbar_installed = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, 
                                          command=self.installed_listbox.yview)
        self.installed_listbox.configure(yscrollcommand=scrollbar_installed.set)
        
        self.installed_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar_installed.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Model info frame
        info_frame = ttk.LabelFrame(installed_frame, text="Model Information", padding="5")
        info_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
        info_frame.columnconfigure(0, weight=1)
        
        self.model_info_text = scrolledtext.ScrolledText(info_frame, height=4, width=40)
        self.model_info_text.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        # Test results frame
        test_frame = ttk.LabelFrame(installed_frame, text="Test Results", padding="5")
        test_frame.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
        test_frame.columnconfigure(0, weight=1)
        
        self.test_results_text = scrolledtext.ScrolledText(test_frame, height=4, width=40)
        self.test_results_text.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        # Bind selection event
        self.installed_listbox.bind('<<ListboxSelect>>', self.on_installed_model_select)
        
        # Button frame for Test and Remove buttons
        button_frame = ttk.Frame(installed_frame)
        button_frame.grid(row=5, column=0, pady=(10, 0))
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=1)
        
        # Test button
        test_btn = ttk.Button(button_frame, text="Test Model", 
                             command=self.test_selected_model)
        test_btn.grid(row=0, column=0, padx=(0, 5), sticky=(tk.W, tk.E))
        
        # Remove button
        remove_btn = ttk.Button(button_frame, text="Remove Model", 
                               command=self.remove_selected_model)
        remove_btn.grid(row=0, column=1, padx=(5, 0), sticky=(tk.W, tk.E))
    
    def create_available_models_panel(self, parent):
        """Create the available models panel"""
        # Available models frame
        available_frame = ttk.LabelFrame(parent, text="Available Models", padding="10")
        available_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(10, 0))
        available_frame.columnconfigure(0, weight=1)
        available_frame.rowconfigure(1, weight=1)
        
        # Search frame
        search_frame = ttk.Frame(available_frame)
        search_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        search_frame.columnconfigure(1, weight=1)
        
        ttk.Label(search_frame, text="Search:").grid(row=0, column=0, padx=(0, 5))
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self.filter_available_models)
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        search_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 5))
        
        # Refresh button for available models
        refresh_available_btn = ttk.Button(search_frame, text="Refresh", 
                                          command=self.refresh_available_models)
        refresh_available_btn.grid(row=0, column=2)
        
        # Available models treeview
        tree_frame = ttk.Frame(available_frame)
        tree_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)
        
        columns = ('Name', 'Size', 'Family', 'Age')
        self.available_tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=15)
        
        # Configure columns with sorting
        self.available_tree.heading('Name', text='Name', command=lambda: self.sort_treeview('Name', False))
        self.available_tree.heading('Size', text='Size', command=lambda: self.sort_treeview('Size', False))
        self.available_tree.heading('Family', text='Family', command=lambda: self.sort_treeview('Family', False))
        self.available_tree.heading('Age', text='Age', command=lambda: self.sort_treeview('Age', False))
        
        self.available_tree.column('Name', width=180)
        self.available_tree.column('Size', width=80)
        self.available_tree.column('Family', width=120)
        self.available_tree.column('Age', width=100)
        
        # Track sorting state
        self.sort_column = None
        self.sort_reverse = False
        
        scrollbar_available = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, 
                                          command=self.available_tree.yview)
        self.available_tree.configure(yscrollcommand=scrollbar_available.set)
        
        self.available_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar_available.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Bind selection event
        self.available_tree.bind('<<TreeviewSelect>>', self.on_available_model_select)
        
        # Model description frame
        desc_frame = ttk.LabelFrame(available_frame, text="Model Description", padding="5")
        desc_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
        desc_frame.columnconfigure(0, weight=1)
        
        self.model_desc_text = scrolledtext.ScrolledText(desc_frame, height=6, width=40)
        self.model_desc_text.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        # Install button
        install_btn = ttk.Button(available_frame, text="Install Selected Model", 
                                command=self.install_selected_model)
        install_btn.grid(row=3, column=0, pady=(10, 0))
    
    def refresh_installed_models(self):
        """Refresh the list of installed models"""
        self.status_var.set("Refreshing installed models...")
        
        def fetch_models():
            try:
                response = requests.get(f"{self.ollama_url}/api/tags", timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    models = data.get('models', [])
                    
                    # Update GUI in main thread
                    self.root.after(0, self.update_installed_models_list, models)
                    self.root.after(0, lambda: self.status_var.set(f"Found {len(models)} installed models"))
                else:
                    self.root.after(0, lambda: self.status_var.set("Error: Could not connect to Ollama"))
            except requests.exceptions.RequestException as e:
                self.root.after(0, lambda: self.status_var.set(f"Error: {str(e)}"))
        
        threading.Thread(target=fetch_models, daemon=True).start()
    
    def update_installed_models_list(self, models):
        """Update the installed models listbox"""
        self.installed_models_data = models
        self.installed_listbox.delete(0, tk.END)
        
        for model in models:
            name = model.get('name', 'Unknown')
            size = model.get('size', 0)
            size_mb = size / (1024 * 1024) if size > 0 else 0
            display_text = f"{name} ({size_mb:.1f} MB)"
            self.installed_listbox.insert(tk.END, display_text)
    
    def on_installed_model_select(self, event):
        """Handle selection of installed model"""
        selection = self.installed_listbox.curselection()
        if not selection:
            return
        
        index = selection[0]
        if index < len(self.installed_models_data):
            model = self.installed_models_data[index]
            self.display_model_info(model)
            # Clear previous test results when selecting a new model
            self.test_results_text.delete(1.0, tk.END)
            self.test_results_text.insert(1.0, "Select 'Test Model' to verify this model is working.")
    
    def display_model_info(self, model):
        """Display detailed information about a model"""
        self.model_info_text.delete(1.0, tk.END)
        
        info = f"Name: {model.get('name', 'Unknown')}\n"
        info += f"Size: {model.get('size', 0) / (1024 * 1024):.1f} MB\n"
        info += f"Modified: {model.get('modified_at', 'Unknown')}\n"
        info += f"Digest: {model.get('digest', 'Unknown')[:16]}...\n\n"
        
        details = model.get('details', {})
        if details:
            info += "Details:\n"
            info += f"  Format: {details.get('format', 'Unknown')}\n"
            info += f"  Family: {details.get('family', 'Unknown')}\n"
            info += f"  Parameters: {details.get('parameter_size', 'Unknown')}\n"
            info += f"  Quantization: {details.get('quantization_level', 'Unknown')}\n"
        
        self.model_info_text.insert(1.0, info)
    
    def remove_selected_model(self):
        """Remove the selected model"""
        selection = self.installed_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a model to remove.")
            return
        
        index = selection[0]
        if index >= len(self.installed_models_data):
            return
        
        model = self.installed_models_data[index]
        model_name = model.get('name', '')
        
        if not model_name:
            messagebox.showerror("Error", "Invalid model name.")
            return
        
        # Confirm deletion
        result = messagebox.askyesno("Confirm Deletion", 
                                   f"Are you sure you want to remove '{model_name}'?\n\n"
                                   f"This action cannot be undone.")
        if not result:
            return
        
        self.status_var.set(f"Removing {model_name}...")
        
        def remove_model():
            try:
                # Use API to delete model
                response = requests.delete(f"{self.ollama_url}/api/delete", 
                                         json={"name": model_name}, timeout=60)
                
                if response.status_code == 200:
                    self.root.after(0, lambda: self.status_var.set(f"Successfully removed {model_name}"))
                    self.root.after(0, self.refresh_installed_models)
                else:
                    error_msg = f"Failed to remove model: {response.text}"
                    self.root.after(0, lambda: self.status_var.set(error_msg))
                    self.root.after(0, lambda: messagebox.showerror("Error", error_msg))
            except requests.exceptions.RequestException as e:
                error_msg = f"Error removing model: {str(e)}"
                self.root.after(0, lambda: self.status_var.set(error_msg))
                self.root.after(0, lambda: messagebox.showerror("Error", error_msg))
        
        threading.Thread(target=remove_model, daemon=True).start()
    
    def test_selected_model(self):
        """Test the selected model with a simple prompt"""
        selection = self.installed_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a model to test.")
            return
        
        index = selection[0]
        if index >= len(self.installed_models_data):
            return
        
        model = self.installed_models_data[index]
        model_name = model.get('name', '')
        
        if not model_name:
            messagebox.showerror("Error", "Invalid model name.")
            return
        
        # Clear previous test results
        self.test_results_text.delete(1.0, tk.END)
        self.test_results_text.insert(1.0, "Testing model... Please wait.")
        
        self.status_var.set(f"Testing {model_name}...")
        
        def test_model():
            try:
                # Test the model with a simple prompt
                test_prompt = "Please say hello"
                
                response = requests.post(f"{self.ollama_url}/api/generate", 
                                       json={
                                           "model": model_name,
                                           "prompt": test_prompt,
                                           "stream": False
                                       }, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    response_text = data.get('response', 'No response received')
                    
                    # Update test results
                    self.root.after(0, lambda: self.test_results_text.delete(1.0, tk.END))
                    self.root.after(0, lambda: self.test_results_text.insert(1.0, 
                        f"Test Prompt: {test_prompt}\n\nModel Response:\n{response_text}"))
                    
                    self.root.after(0, lambda: self.status_var.set(f"Test completed for {model_name}"))
                    
                else:
                    error_msg = f"Test failed: {response.text}"
                    self.root.after(0, lambda: self.test_results_text.delete(1.0, tk.END))
                    self.root.after(0, lambda: self.test_results_text.insert(1.0, f"Test failed: {error_msg}"))
                    self.root.after(0, lambda: self.status_var.set(f"Test failed for {model_name}"))
                    
            except requests.exceptions.RequestException as e:
                error_msg = f"Connection error: {str(e)}"
                self.root.after(0, lambda: self.test_results_text.delete(1.0, tk.END))
                self.root.after(0, lambda: self.test_results_text.insert(1.0, f"Test failed: {error_msg}"))
                self.root.after(0, lambda: self.status_var.set(f"Test failed for {model_name}"))
            except Exception as e:
                error_msg = f"Unexpected error: {str(e)}"
                self.root.after(0, lambda: self.test_results_text.delete(1.0, tk.END))
                self.root.after(0, lambda: self.test_results_text.insert(1.0, f"Test failed: {error_msg}"))
                self.root.after(0, lambda: self.status_var.set(f"Test failed for {model_name}"))
        
        threading.Thread(target=test_model, daemon=True).start()
    
    def show_progress(self):
        """Show download status area"""
        self.download_status_frame.grid()
        self.cancel_download_btn.grid()
        self.resume_download_btn.grid_remove()
        self.progress_var.set(0)
        self.progress_label_var.set("")
        self.download_status_var.set("")
    
    def hide_progress(self):
        """Hide download status area"""
        self.download_status_frame.grid_remove()
        self.cancel_download_btn.grid_remove()
        self.resume_download_btn.grid_remove()
    
    def show_resume_option(self):
        """Show resume button when download is interrupted"""
        self.cancel_download_btn.grid_remove()
        self.resume_download_btn.grid()
    
    def cancel_download(self):
        """Cancel the current download"""
        if self.download_active:
            self.download_active = False
            self.status_var.set("Download cancelled by user")
            self.update_download_status("Download cancelled - click Resume to continue")
            self.show_resume_option()
            messagebox.showinfo("Download Cancelled", "The download has been cancelled. You can resume it later.")
    
    def resume_download(self):
        """Resume the interrupted download"""
        if self.current_download_model:
            self.status_var.set(f"Resuming download of {self.current_download_model}...")
            self.update_download_status(f"Resuming download of {self.current_download_model}...")
            self.download_active = True
            self.cancel_download_btn.grid()
            self.resume_download_btn.grid_remove()
            
            # Start the download process again
            self.install_model_by_name(self.current_download_model)
        else:
            messagebox.showwarning("No Download to Resume", "No interrupted download found to resume.")
    
    def update_progress(self, percentage, message=""):
        """Update progress bar and message"""
        self.progress_var.set(percentage)
        if message:
            self.progress_label_var.set(message)
    
    def update_download_status(self, status_message):
        """Update the main download status message"""
        self.download_status_var.set(status_message)
    
    def sort_treeview(self, col, reverse):
        """Sort treeview by column"""
        # Get all items from the treeview
        items = [(self.available_tree.set(child, col), child) for child in self.available_tree.get_children('')]
        
        # Determine if we're sorting the same column
        if self.sort_column == col:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_reverse = False
            self.sort_column = col
        
        # Sort the items
        if col == 'Size':
            # Special handling for size column - extract numeric value
            def size_key(item):
                size_str = item[0]
                if 'B' in size_str:
                    # Extract number and convert to bytes for comparison
                    num_str = size_str.replace('B', '').strip()
                    if 'K' in num_str:
                        return float(num_str.replace('K', '')) * 1024
                    elif 'M' in num_str:
                        return float(num_str.replace('M', '')) * 1024 * 1024
                    elif 'G' in num_str:
                        return float(num_str.replace('G', '')) * 1024 * 1024 * 1024
                    else:
                        return float(num_str)
                return 0
            
            items.sort(key=size_key, reverse=self.sort_reverse)
        elif col == 'Age':
            # Special handling for age column - sort by date
            def age_key(item):
                age_str = item[0]
                # Convert age string to sortable format (YYYY-MM)
                month_map = {
                    'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04',
                    'May': '05', 'Jun': '06', 'Jul': '07', 'Aug': '08',
                    'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'
                }
                try:
                    parts = age_str.split()
                    if len(parts) == 2:
                        month, year = parts
                        return f"{year}-{month_map.get(month, '00')}"
                    return "0000-00"
                except:
                    return "0000-00"
            
            items.sort(key=age_key, reverse=self.sort_reverse)
        else:
            # Regular string sorting for Name and Family
            items.sort(key=lambda x: x[0].lower(), reverse=self.sort_reverse)
        
        # Rearrange items in sorted positions
        for index, (val, child) in enumerate(items):
            self.available_tree.move(child, '', index)
        
        # Update column headers to show sort direction
        for column in ('Name', 'Size', 'Family', 'Age'):
            if column == col:
                arrow = " ↓" if self.sort_reverse else " ↑"
                self.available_tree.heading(column, text=column + arrow)
            else:
                self.available_tree.heading(column, text=column)

    def load_available_models(self):
        """Load available models from Ollama registry and fallback to curated list"""
        self.status_var.set("Loading available models...")
        
        def fetch_models_from_registry():
            try:
                # Try to fetch from Ollama's model registry
                response = requests.get("https://ollama.com/models", timeout=10)
                if response.status_code == 200:
                    # For now, we'll use the curated list but mark it as dynamic
                    self.root.after(0, self.load_curated_models)
                    self.root.after(0, lambda: self.status_var.set("Loaded available models (curated list)"))
                else:
                    self.root.after(0, self.load_curated_models)
                    self.root.after(0, lambda: self.status_var.set("Loaded available models (offline mode)"))
            except:
                # Fallback to curated list if network fails
                self.root.after(0, self.load_curated_models)
                self.root.after(0, lambda: self.status_var.set("Loaded available models (offline mode)"))
        
        threading.Thread(target=fetch_models_from_registry, daemon=True).start()
    
    def load_curated_models(self):
        """Load curated list of popular Ollama models with updated information"""
        self.available_models = {
            "llama3.2:latest": {
                "name": "llama3.2:latest",
                "size": "3.1GB",
                "family": "llama",
                "age": "Sep 2024",
                "description": "Meta's Llama 3.2 - Latest version with improved performance and capabilities. Good for general conversation and reasoning tasks."
            },
            "llama3.2:3b": {
                "name": "llama3.2:3b",
                "size": "3.1GB",
                "family": "llama",
                "age": "Sep 2024",
                "description": "Meta's Llama 3.2 3B parameter model. Lightweight and fast, suitable for resource-constrained environments."
            },
            "llama3.2:1b": {
                "name": "llama3.2:1b",
                "size": "1.3GB",
                "family": "llama",
                "age": "Sep 2024",
                "description": "Meta's Llama 3.2 1B parameter model. Ultra-lightweight model for basic tasks and quick responses."
            },
            "llama4:latest": {
                "name": "llama4:latest",
                "size": "65.0GB",
                "family": "llama",
                "age": "Jan 2025",
                "description": "Meta's Llama 4 Scout - 109B parameter multimodal model with vision capabilities. Latest and most advanced model from Meta."
            },
            "llama3.1:latest": {
                "name": "llama3.1:latest",
                "size": "4.7GB",
                "family": "llama",
                "age": "Jul 2024",
                "description": "Meta's Llama 3.1 - Previous generation with strong performance. Good balance of capability and resource usage."
            },
            "llama3.1:8b": {
                "name": "llama3.1:8b",
                "size": "4.7GB",
                "family": "llama",
                "age": "Jul 2024",
                "description": "Meta's Llama 3.1 8B parameter model. More capable than 3B version, suitable for complex tasks."
            },
            "llama3.1:70b": {
                "name": "llama3.1:70b",
                "size": "40.2GB",
                "family": "llama",
                "age": "Jul 2024",
                "description": "Meta's Llama 3.1 70B parameter model. High-performance model for demanding tasks. Requires significant resources."
            },
            "codellama:latest": {
                "name": "codellama:latest",
                "size": "3.8GB",
                "family": "llama",
                "age": "Aug 2023",
                "description": "Meta's Code Llama - Specialized for code generation, completion, and debugging. Excellent for programming tasks."
            },
            "codellama:7b": {
                "name": "codellama:7b",
                "size": "3.8GB",
                "family": "llama",
                "age": "Aug 2023",
                "description": "Code Llama 7B - Specialized coding model with good performance for most programming tasks."
            },
            "codellama:13b": {
                "name": "codellama:13b",
                "size": "7.3GB",
                "family": "llama",
                "age": "Aug 2023",
                "description": "Code Llama 13B - More capable coding model for complex programming tasks and code analysis."
            },
            "codellama:34b": {
                "name": "codellama:34b",
                "size": "19.0GB",
                "family": "llama",
                "age": "Aug 2023",
                "description": "Code Llama 34B - High-performance coding model for advanced programming tasks. Requires significant resources."
            },
            "mistral:latest": {
                "name": "mistral:latest",
                "size": "4.1GB",
                "family": "mistral",
                "age": "Sep 2023",
                "description": "Mistral 7B - Efficient and capable model from Mistral AI. Good for general tasks with lower resource requirements."
            },
            "mistral:7b": {
                "name": "mistral:7b",
                "size": "4.1GB",
                "family": "mistral",
                "age": "Sep 2023",
                "description": "Mistral 7B - High-quality model with excellent performance-to-size ratio. Great for general conversation."
            },
            "mistral-magistral:latest": {
                "name": "mistral-magistral:latest",
                "size": "8.2GB",
                "family": "mistral",
                "age": "Jan 2025",
                "description": "Mistral Magistral - Latest model from Mistral AI with enhanced capabilities and improved performance."
            },
            "mistral-small-3.1:latest": {
                "name": "mistral-small-3.1:latest",
                "size": "4.1GB",
                "family": "mistral",
                "age": "Jan 2025",
                "description": "Mistral Small 3.1 - Enhanced long-context model supporting 128k tokens with improved performance."
            },
            "mixtral:latest": {
                "name": "mixtral:latest",
                "size": "26.2GB",
                "family": "mixtral",
                "age": "Dec 2023",
                "description": "Mixtral 8x7B - Mixture of Experts model with 8 experts. Excellent performance for complex reasoning tasks."
            },
            "mixtral:8x7b": {
                "name": "mixtral:8x7b",
                "size": "26.2GB",
                "family": "mixtral",
                "age": "Dec 2023",
                "description": "Mixtral 8x7B - Advanced mixture of experts model. High performance but requires significant resources."
            },
            "gemma:latest": {
                "name": "gemma:latest",
                "size": "5.4GB",
                "family": "gemma",
                "age": "Feb 2024",
                "description": "Google's Gemma 7B - Open-source model with strong performance. Good for general tasks and research."
            },
            "gemma:7b": {
                "name": "gemma:7b",
                "size": "5.4GB",
                "family": "gemma",
                "age": "Feb 2024",
                "description": "Google Gemma 7B - Efficient model with good capabilities for various tasks."
            },
            "gemma:2b": {
                "name": "gemma:2b",
                "size": "1.6GB",
                "family": "gemma",
                "age": "Feb 2024",
                "description": "Google Gemma 2B - Lightweight model for basic tasks and resource-constrained environments."
            },
            "gemma3:latest": {
                "name": "gemma3:latest",
                "size": "8.5GB",
                "family": "gemma",
                "age": "Jan 2025",
                "description": "Google's Gemma 3 - Latest version with enhanced capabilities and vision support. Available in multiple sizes."
            },
            "phi3:latest": {
                "name": "phi3:latest",
                "size": "2.3GB",
                "family": "phi",
                "age": "Apr 2024",
                "description": "Microsoft's Phi-3 - Small but capable model. Good for mobile and edge computing applications."
            },
            "phi3:mini": {
                "name": "phi3:mini",
                "size": "2.3GB",
                "family": "phi",
                "age": "Apr 2024",
                "description": "Microsoft Phi-3 Mini - Compact model with surprising capabilities. Great for quick tasks."
            },
            "phi3:medium": {
                "name": "phi3:medium",
                "size": "14.3GB",
                "family": "phi",
                "age": "Apr 2024",
                "description": "Microsoft Phi-3 Medium - More capable version of Phi-3. Good balance of performance and efficiency."
            },
            "qwen2.5:latest": {
                "name": "qwen2.5:latest",
                "size": "4.4GB",
                "family": "qwen",
                "age": "Jun 2024",
                "description": "Alibaba's Qwen2.5 7B - Strong multilingual model with good reasoning capabilities."
            },
            "qwen2.5:7b": {
                "name": "qwen2.5:7b",
                "size": "4.4GB",
                "family": "qwen",
                "age": "Jun 2024",
                "description": "Qwen2.5 7B - Capable model with strong multilingual support and reasoning abilities."
            },
            "qwen2.5:14b": {
                "name": "qwen2.5:14b",
                "size": "8.7GB",
                "family": "qwen",
                "age": "Jun 2024",
                "description": "Qwen2.5 14B - More powerful version with enhanced capabilities for complex tasks."
            },
            "qwen2.5:32b": {
                "name": "qwen2.5:32b",
                "size": "19.2GB",
                "family": "qwen",
                "age": "Jun 2024",
                "description": "Qwen2.5 32B - High-performance model with advanced reasoning capabilities. Requires significant resources."
            },
            "qwen2.5-vl:latest": {
                "name": "qwen2.5-vl:latest",
                "size": "4.4GB",
                "family": "qwen",
                "age": "Jan 2025",
                "description": "Qwen2.5 VL - Vision-language model for document scanning, OCR, and multilingual translation tasks."
            },
            "deepseek-r1:latest": {
                "name": "deepseek-r1:latest",
                "size": "4.1GB",
                "family": "deepseek",
                "age": "Jan 2025",
                "description": "DeepSeek-R1 - Open reasoning model with performance approaching leading models like O3 and Gemini 2.5 Pro."
            },
            "neural-chat:latest": {
                "name": "neural-chat:latest",
                "size": "4.1GB",
                "family": "neural",
                "age": "Nov 2023",
                "description": "Intel's Neural Chat - Optimized for conversational AI with good performance on dialogue tasks."
            },
            "orca-mini:latest": {
                "name": "orca-mini:latest",
                "size": "1.9GB",
                "family": "orca",
                "age": "Jun 2023",
                "description": "Microsoft's Orca Mini - Lightweight model trained on high-quality data. Good for educational purposes."
            },
            "dolphin-2.6-mistral:latest": {
                "name": "dolphin-2.6-mistral:latest",
                "size": "4.1GB",
                "family": "dolphin",
                "age": "Dec 2023",
                "description": "Dolphin 2.6 Mistral - Uncensored and helpful model based on Mistral. Good for creative and unrestricted tasks."
            },
            "dolphin-mistral:latest": {
                "name": "dolphin-mistral:latest",
                "size": "4.1GB",
                "family": "dolphin",
                "age": "Nov 2023",
                "description": "Dolphin Mistral 7B - Popular uncensored model based on Mistral 7B. Great for creative writing and unrestricted conversations."
            },
            "dolphin-2.7-mixtral:latest": {
                "name": "dolphin-2.7-mixtral:latest",
                "size": "26.2GB",
                "family": "dolphin",
                "age": "Jan 2024",
                "description": "Dolphin 2.7 Mixtral - Advanced uncensored model based on Mixtral 8x7B. High performance for complex creative tasks."
            },
            "openchat:latest": {
                "name": "openchat:latest",
                "size": "4.1GB",
                "family": "openchat",
                "age": "Aug 2023",
                "description": "OpenChat - Open-source conversational AI model with good dialogue capabilities."
            },
            "starling-lm:latest": {
                "name": "starling-lm:latest",
                "size": "4.1GB",
                "family": "starling",
                "age": "Oct 2023",
                "description": "Starling LM - High-quality conversational model with strong performance on dialogue tasks."
            },
            "wizard-vicuna:latest": {
                "name": "wizard-vicuna:latest",
                "size": "4.1GB",
                "family": "wizard",
                "age": "May 2023",
                "description": "Wizard Vicuna - Instruction-tuned model with good performance on various tasks."
            },
            "vicuna:latest": {
                "name": "vicuna:latest",
                "size": "4.1GB",
                "family": "vicuna",
                "age": "Mar 2023",
                "description": "Vicuna - Open-source chat model fine-tuned from LLaMA. Good for general conversation."
            },
            "alpaca:latest": {
                "name": "alpaca:latest",
                "size": "4.1GB",
                "family": "alpaca",
                "age": "Mar 2023",
                "description": "Alpaca - Stanford's instruction-following model based on LLaMA. Good for following instructions."
            },
            "nous-hermes:latest": {
                "name": "nous-hermes:latest",
                "size": "4.1GB",
                "family": "nous",
                "age": "Jul 2023",
                "description": "Nous Hermes - High-quality instruction-tuned model with excellent reasoning capabilities."
            },
            "airoboros:latest": {
                "name": "airoboros:latest",
                "size": "4.1GB",
                "family": "airoboros",
                "age": "Aug 2023",
                "description": "Airoboros - Instruction-tuned model with strong performance on various tasks and good reasoning."
            },
            "llava:latest": {
                "name": "llava:latest",
                "size": "4.1GB",
                "family": "llava",
                "age": "Nov 2023",
                "description": "LLaVA - Large Language and Vision Assistant. Multimodal model for text and image understanding."
            },
            "bakllava:latest": {
                "name": "bakllava:latest",
                "size": "4.1GB",
                "family": "bakllava",
                "age": "Oct 2023",
                "description": "BakLLaVA - Enhanced vision-language model with improved multimodal capabilities."
            }
        }
        
        self.update_available_models_tree()
        self.status_var.set(f"Loaded {len(self.available_models)} available models")
    
    def refresh_available_models(self):
        """Refresh the available models list"""
        self.status_var.set("Refreshing available models...")
        
        def refresh_models():
            try:
                # Try to fetch from Ollama's model registry
                response = requests.get("https://ollama.com/models", timeout=10)
                if response.status_code == 200:
                    # For now, we'll reload the curated list but could parse the response in the future
                    self.root.after(0, self.load_curated_models)
                    self.root.after(0, lambda: self.status_var.set(f"Refreshed - {len(self.available_models)} models available"))
                else:
                    self.root.after(0, self.load_curated_models)
                    self.root.after(0, lambda: self.status_var.set(f"Refreshed - {len(self.available_models)} models available (offline mode)"))
            except:
                # Fallback to curated list if network fails
                self.root.after(0, self.load_curated_models)
                self.root.after(0, lambda: self.status_var.set(f"Refreshed - {len(self.available_models)} models available (offline mode)"))
        
        threading.Thread(target=refresh_models, daemon=True).start()
    
    def update_available_models_tree(self):
        """Update the available models treeview"""
        # Clear existing items
        for item in self.available_tree.get_children():
            self.available_tree.delete(item)
        
        # Add models to tree
        for model_name, model_data in self.available_models.items():
            self.available_tree.insert('', 'end', values=(
                model_data['name'],
                model_data['size'],
                model_data['family'],
                model_data['age']
            ))
    
    def filter_available_models(self, *args):
        """Filter available models based on search term"""
        search_term = self.search_var.get().lower()
        
        # Clear existing items
        for item in self.available_tree.get_children():
            self.available_tree.delete(item)
        
        # Add filtered models
        for model_name, model_data in self.available_models.items():
            if (search_term in model_name.lower() or 
                search_term in model_data['family'].lower() or
                search_term in model_data['description'].lower()):
                self.available_tree.insert('', 'end', values=(
                    model_data['name'],
                    model_data['size'],
                    model_data['family'],
                    model_data['age']
                ))
        
        # Reapply current sort if any
        if self.sort_column:
            self.sort_treeview(self.sort_column, self.sort_reverse)
    
    def on_available_model_select(self, event):
        """Handle selection of available model"""
        selection = self.available_tree.selection()
        if not selection:
            return
        
        item = self.available_tree.item(selection[0])
        model_name = item['values'][0]
        
        if model_name in self.available_models:
            model_data = self.available_models[model_name]
            self.display_model_description(model_data)
    
    def display_model_description(self, model_data):
        """Display model description"""
        self.model_desc_text.delete(1.0, tk.END)
        
        desc = f"Name: {model_data['name']}\n"
        desc += f"Size: {model_data['size']}\n"
        desc += f"Family: {model_data['family']}\n\n"
        desc += f"Description:\n{model_data['description']}\n\n"
        desc += "Note: Model sizes are approximate and may vary based on quantization."
        
        self.model_desc_text.insert(1.0, desc)
    
    def install_selected_model(self):
        """Install the selected model"""
        if self.download_active:
            messagebox.showwarning("Download in Progress", "Please wait for the current download to complete.")
            return
            
        selection = self.available_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a model to install.")
            return
        
        item = self.available_tree.item(selection[0])
        model_name = item['values'][0]
        
        if not model_name:
            messagebox.showerror("Error", "Invalid model name.")
            return
        
        # Confirm installation
        result = messagebox.askyesno("Confirm Installation", 
                                   f"Are you sure you want to install '{model_name}'?\n\n"
                                   f"This may take several minutes depending on your internet connection.")
        if not result:
            return
        
        # Start download
        self.download_active = True
        self.current_download_model = model_name
        self.status_var.set(f"Starting download of {model_name}...")
        self.show_progress()
        self.update_download_status(f"Preparing to download {model_name}...")
        
        # Use the new install_model_by_name method
        self.install_model_by_name(model_name)
    
    def install_model_by_name(self, model_name):
        """Install a model by name (used for resuming downloads)"""
        def install_model():
            try:
                # First, test if Ollama is running and accessible
                self.root.after(0, lambda: self.update_download_status("Testing connection to Ollama..."))
                test_response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
                if test_response.status_code != 200:
                    raise Exception("Cannot connect to Ollama - make sure it's running")
                
                self.root.after(0, lambda: self.update_download_status("Connection OK, starting download..."))
                
                # Use streaming API for resumable downloads with real progress
                self.root.after(0, lambda: self.update_download_status("Starting resumable download..."))
                
                # Use streaming API to pull model with progress tracking
                # Set a reasonable timeout for the initial connection
                response = requests.post(f"{self.ollama_url}/api/pull", 
                                       json={"name": model_name}, 
                                       stream=True, timeout=30)
                
                if response.status_code == 200:
                    total_size = None
                    downloaded_size = 0
                    manifest_start_time = None
                    last_update_time = time.time()
                    download_start_time = time.time()
                    last_completed = 0
                    
                    for line in response.iter_lines():
                        # Check if download was cancelled
                        if not self.download_active:
                            break
                            
                        if not line:
                            continue
                        
                        # Check for timeout - if no updates for 60 seconds, consider it stuck
                        current_time = time.time()
                        if current_time - last_update_time > 60:
                            self.root.after(0, lambda: self.status_var.set(f"Download appears stuck - no updates for 60 seconds"))
                            self.root.after(0, lambda: self.update_download_status(f"Download may be stuck. Check your internet connection or click Cancel."))
                            break
                            
                        try:
                            data = json.loads(line.decode('utf-8'))
                            last_update_time = time.time()  # Update timestamp when we get any response
                            
                            # Update status based on response
                            if 'status' in data:
                                status = data['status']
                                
                                if status == 'pulling manifest':
                                    if manifest_start_time is None:
                                        manifest_start_time = time.time()
                                        self.root.after(0, lambda: self.status_var.set(f"Downloading manifest for {model_name}..."))
                                        self.root.after(0, lambda: self.update_download_status(f"Downloading manifest for {model_name}..."))
                                        self.root.after(0, lambda: self.update_progress(5, "Getting manifest - this should be quick"))
                                    else:
                                        # Show how long manifest has been downloading
                                        elapsed = time.time() - manifest_start_time
                                        if elapsed > 30:  # If manifest takes more than 30 seconds
                                            self.root.after(0, lambda: self.update_download_status(f"Manifest download taking longer than expected ({elapsed:.0f}s) - check connection"))
                                    
                                elif status == 'downloading':
                                    if 'total' in data and 'completed' in data:
                                        total = data['total']
                                        completed = data['completed']
                                        percentage = (completed / total) * 100
                                        
                                        # Convert bytes to human readable
                                        total_mb = total / (1024 * 1024)
                                        completed_mb = completed / (1024 * 1024)
                                        
                                        # Calculate download speed and remaining time
                                        elapsed_time = time.time() - download_start_time
                                        if completed > last_completed and elapsed_time > 0:
                                            # Calculate speed in MB/s
                                            speed_mbps = (completed - last_completed) / (1024 * 1024) / 2  # Assuming 2-second intervals
                                            remaining_bytes = total - completed
                                            if speed_mbps > 0:
                                                remaining_seconds = remaining_bytes / (1024 * 1024) / speed_mbps
                                                if remaining_seconds < 60:
                                                    speed_info = f" ({speed_mbps:.1f} MB/s, ~{remaining_seconds:.0f}s remaining)"
                                                else:
                                                    speed_info = f" ({speed_mbps:.1f} MB/s, ~{remaining_seconds/60:.1f}m remaining)"
                                            else:
                                                speed_info = " (calculating speed...)"
                                        else:
                                            speed_info = ""
                                        
                                        last_completed = completed
                                        
                                        self.root.after(0, lambda: self.status_var.set(
                                            f"Downloading {model_name}: {completed_mb:.1f}MB / {total_mb:.1f}MB"))
                                        self.root.after(0, lambda: self.update_download_status(
                                            f"Downloading {model_name}: {completed_mb:.1f}MB / {total_mb:.1f}MB{speed_info}"))
                                        self.root.after(0, lambda: self.update_progress(
                                            percentage, f"{completed_mb:.1f}MB / {total_mb:.1f}MB"))
                                    else:
                                        # Show that we're downloading but don't have progress info yet
                                        self.root.after(0, lambda: self.update_download_status(f"Downloading {model_name}..."))
                                        self.root.after(0, lambda: self.update_progress(10, "Downloading..."))
                                
                                elif status == 'verifying sha256 digest':
                                    self.root.after(0, lambda: self.status_var.set(f"Verifying {model_name}..."))
                                    self.root.after(0, lambda: self.update_download_status(f"Verifying {model_name}..."))
                                    self.root.after(0, lambda: self.update_progress(95, "Verifying download"))
                                    
                                elif status == 'writing manifest':
                                    self.root.after(0, lambda: self.status_var.set(f"Finalizing {model_name}..."))
                                    self.root.after(0, lambda: self.update_download_status(f"Finalizing {model_name}..."))
                                    self.root.after(0, lambda: self.update_progress(98, "Writing manifest"))
                                    
                                elif status == 'removing any unused layers':
                                    self.root.after(0, lambda: self.status_var.set(f"Cleaning up {model_name}..."))
                                    self.root.after(0, lambda: self.update_download_status(f"Cleaning up {model_name}..."))
                                    self.root.after(0, lambda: self.update_progress(99, "Cleaning up"))
                                    
                                elif status == 'success':
                                    self.root.after(0, lambda: self.status_var.set(f"Successfully installed {model_name}"))
                                    self.root.after(0, lambda: self.update_download_status(f"Successfully installed {model_name}!"))
                                    self.root.after(0, lambda: self.update_progress(100, "Download complete!"))
                                    self.root.after(0, self.hide_progress)
                                    
                                    # Verify installation by refreshing and checking if model appears
                                    self.root.after(0, self.verify_installation, model_name)
                                    break
                                    
                        except json.JSONDecodeError:
                            continue
                        except Exception as e:
                            # Log error but continue processing
                            self.root.after(0, lambda: self.status_var.set(f"Warning: Error parsing response - {str(e)}"))
                            continue
                
                else:
                    error_msg = f"Failed to install model: {response.text}"
                    self.root.after(0, lambda: self.status_var.set(error_msg))
                    self.root.after(0, lambda: self.hide_progress())
                    self.root.after(0, lambda: messagebox.showerror("Error", error_msg))
                    
            except requests.exceptions.RequestException as e:
                error_msg = f"API download failed: {str(e)}"
                self.root.after(0, lambda: self.status_var.set(error_msg))
                self.root.after(0, lambda: self.update_download_status("API failed, trying CLI method..."))
                
                # Try CLI method as fallback
                try:
                    self.root.after(0, lambda: self.update_download_status("Using CLI method to download..."))
                    result = subprocess.run(['ollama', 'pull', model_name], 
                                          capture_output=True, text=True, timeout=600)
                    
                    if result.returncode == 0:
                        self.root.after(0, lambda: self.status_var.set(f"Successfully installed {model_name} via CLI"))
                        self.root.after(0, lambda: self.update_download_status(f"Successfully installed {model_name}!"))
                        self.root.after(0, lambda: self.update_progress(100, "Download complete!"))
                        self.root.after(0, self.hide_progress)
                        self.root.after(0, self.verify_installation, model_name)
                    else:
                        error_msg = f"CLI download also failed: {result.stderr}"
                        self.root.after(0, lambda: self.status_var.set(error_msg))
                        self.root.after(0, lambda: self.hide_progress())
                        self.root.after(0, lambda: messagebox.showerror("Error", error_msg))
                except subprocess.TimeoutExpired:
                    error_msg = "Download timed out after 10 minutes"
                    self.root.after(0, lambda: self.status_var.set(error_msg))
                    self.root.after(0, lambda: self.hide_progress())
                    self.root.after(0, lambda: messagebox.showerror("Error", error_msg))
                except Exception as cli_error:
                    error_msg = f"CLI download failed: {str(cli_error)}"
                    self.root.after(0, lambda: self.status_var.set(error_msg))
                    self.root.after(0, lambda: self.hide_progress())
                    self.root.after(0, lambda: messagebox.showerror("Error", error_msg))
            except Exception as e:
                error_msg = f"Unexpected error: {str(e)}"
                self.root.after(0, lambda: self.status_var.set(error_msg))
                self.root.after(0, lambda: self.hide_progress())
                self.root.after(0, lambda: messagebox.showerror("Error", error_msg))
            finally:
                self.download_active = False
                self.current_download_model = None
        
        threading.Thread(target=install_model, daemon=True).start()
    
    def verify_installation(self, model_name):
        """Verify that the model was actually installed"""
        def check_installation():
            try:
                # Refresh the installed models list
                response = requests.get(f"{self.ollama_url}/api/tags", timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    models = data.get('models', [])
                    
                    # Check if the model is in the list
                    model_found = any(model.get('name', '').startswith(model_name.split(':')[0]) for model in models)
                    
                    if model_found:
                        self.refresh_installed_models()
                        messagebox.showinfo("Success", f"Model '{model_name}' installed successfully and verified!")
                    else:
                        messagebox.showwarning("Installation Warning", 
                                             f"Model '{model_name}' download completed but may not be properly installed.\n"
                                             f"Please check your Ollama installation and try again.")
                else:
                    messagebox.showwarning("Verification Failed", 
                                         "Could not verify installation. Please check the installed models list manually.")
            except Exception as e:
                messagebox.showwarning("Verification Error", 
                                     f"Could not verify installation: {str(e)}\n"
                                     f"Please check the installed models list manually.")
        
        # Run verification in a separate thread to avoid blocking
        threading.Thread(target=check_installation, daemon=True).start()

def main():
    """Main function to run the application"""
    root = tk.Tk()
    app = OllamaManager(root)
    
    # Center the window
    root.update_idletasks()
    x = (root.winfo_screenwidth() // 2) - (root.winfo_width() // 2)
    y = (root.winfo_screenheight() // 2) - (root.winfo_height() // 2)
    root.geometry(f"+{x}+{y}")
    
    root.mainloop()

if __name__ == "__main__":
    main()
