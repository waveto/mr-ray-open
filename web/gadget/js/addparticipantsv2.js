/*
Copyright 2011 Acknack Ltd

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
*/
/*
* Description of interface robot can use:
*	set 'waveuid' to base64 json string to trigger the robot to action something
*	'state' is a base64 json string containing the public state and email participants
*	set 'participant-details-state' to fetch to retrieve the participant details
*	'participant-details' contains a base64 json string with participant details
*/
(function($) {
	/*************************************************************************
	* 'Global' variables
	*************************************************************************/
	var documentInitialized = false;
	/**
	* List of actions the wave server understands
	*/
	var actions = {
		addEmail	: "addEmail",
		deleteEmail	: "deleteEmail",
		changePublic: "changePublic" 
	};
	var sentCommand = null;
	
	/**
	* Setting this to true indicates that a user is actioning the gadget and
	* it should not be updated
	*/
	var isActioning = false;
	
	/**
	* Returns true if the gadget can relad
	*/
	var canReloadPage = function() {
		if(isActioning || sentCommand !== null) {
			return false;
		}
		return true;
	}
	
	
	/*************************************************************************
	* Factories / producers
	*************************************************************************/
	/**
	* Used for generating elements convieniently
	* @param elemType: the element type e.g. 'div'
	* @param attr: map containing attributes e.g. {'id': 'myid'}
	* @param elemText: the text to place in the element. false for none
	* @param clickEvent: the event to call when the element is clicked. false for none
	* @return the element
	*/
	var elementFactory = function(elemType, attr, elemText, clickEvent) {
		var elem = $(document.createElement(elemType));
		for(var n in attr) {
			elem.attr(n, attr[n]);	
		}
		if(elemText !== undefined && elemText !== false) {
			elem.text(elemText);	
		}
		if(clickEvent !== undefined && clickEvent !== false) {
			elem.click(clickEvent);	
		}
		return elem;
	};
	
	
	/**
	* Wraps a set of functions that can be called by buttons to accomplish a
	* task
	*/
	var actionFactory = {
		changePublicSettingsButt: function() {
			isActioning = true;
			renderFactory.publicSettings(null);
		},
		deleteEmailUserButt		: function() {
			var users = new Users(wave.getState());
			var button = $(this);
			var email = button.attr("id").replace("deleteemail_", "");
			users.removeEmailUser(email);
			renderFactory.working();
			return false;
		},
		addEmailUserButt		: function() {
			isActioning = true;
			renderFactory.addEmail(null);
		},
		back					: function() {
			isActioning = false;
			renderFactory.list(null);
		},
		submitNewEmail			: function() {
			var users = new Users(wave.getState());
			email = $('#newEmailInput').val();
			message = $('#messageInput').val();
			if(users.addEmailUser(email, message)) {
				renderFactory.working();
			} else {
				if(!users.isEmailValid(email)) {
					$('#emailError').text(email + " does not appear to be a valid e-mail address");
					$('#emailError').attr("style", "");
				}
				if(email.length == 0) {
				    $('#emailError').text("You must enter an e-mail address");
					$('#emailError').attr("style", "");
				}
				if(users.isUserAlreadyAdded(email)) {
					$('#emailError').text(email + " is already a participant of this wave");
					$('#emailError').attr("style", "");
				}
				gadgets.window.adjustHeight();
			}
		},
		submitPublic			: function() {
			var users = new Users(wave.getState());
			var noAccess = $('#publicSettingRadioPrivate').attr("checked");
			var readOnly = $('#publicSettingRadioReadOnly').attr("checked");
			var editable = $('#publicSettingRadioEditable').attr("checked");
			var isPublic = false;
			var isReadOnly = true;
			if (!noAccess) {
				isPublic = true;
			}
			if (editable) {
				isReadOnly = false;
			}
			users.changePublic(isPublic, isReadOnly);
			renderFactory.working();
		}
	};
	
	/**
	* Some commonly used utility methods
	*/
	var utils = {
		/**
		* @return the current viewer id
		*/
		getViewer		: function() {
			return wave.getViewer().getId();
		}
	};
	
	
	/**
	* Functions that can be used to render "pages" in the gadget
	*/
	var renderFactory = {
		list			: 	function(state) {
			state = state || wave.getState();
			var gadgetContent = $('#content');
			var actions = $('#actions');
			gadgetContent.children().remove();
			actions.children().remove();
			var users = new Users(state);
			
			//Public status
			if(users.isPublic()) {
				if(users.isPublicReadOnly()) {
					var readOnlyStateText = "viewable (read only)";
				} else {
					var readOnlyStateText = "editable";
				}
				gadgetContent.append($(
					"<div id='publicStatusContainer' class='attention ui-state-error ui-corner-all'>"+
						"This wave is publicly "+ readOnlyStateText +" using <a href='"+ users.getPublicUrl() +"' target='_blank'>this link</a>." +
					"</div>"
					));
				$('#publicStatusContainer').append(elementFactory("button", {"class":"waveButton ui-state-default ui-corner-all"}, "change", actionFactory.changePublicSettingsButt));
			}
			
			//Email list
			var emailUsers = users.getEmailUsers();
			if (emailUsers.length > 0){
				gadgetContent.append($(
					"<p id='emailUserListTitle'>E-mail participants included in this wave:</p>"+
					"<ul id='emailUserList'>"+
					"</ul>"
				));
			
		
				for(var i=0; i < emailUsers.length; i++) {
					$('#emailUserList').append(
					    elementFactory("li", {}, emailUsers[i], false).append(
					        elementFactory("a",
                				{
                					"href"		: "#",
                					"id"		: "deleteemail_" + emailUsers[i].replace("command_", "")
                				},
                				"delete",
                				actionFactory.deleteEmailUserButt)));
				}
			} else {
			    gadgetContent.append($(
			        "<p>No e-mail participants are included on this Wave. Press add to include some...</p>"));
			}
			
			//Add buttons
			if(!users.isPublic()) {
				actions.append(elementFactory("button", {"class":"waveButton ui-state-default ui-corner-all"}, "make public", actionFactory.changePublicSettingsButt));
			}
			actions.append(elementFactory("button", {"class":"waveButton ui-state-default ui-corner-all"}, "add e-mail participant", actionFactory.addEmailUserButt));
			gadgets.window.adjustHeight();
		},
		publicSettings	: 	function(state) {
			state = state || wave.getState();
			var gadgetContent = $('#content');
			var actions = $('#actions');
			gadgetContent.children().remove();
			actions.children().remove();
			var users = new Users(state);
			
			gadgetContent.append($(
				"<p>Making a Wave public will allow anyone to access it from the public url. If you are unsure what to do it is recommended that you press back.</p>"+
				"<form id='publicSettingsForm'>"+
						"<p><input type='radio' name='publicSettings' value='d' id='publicSettingRadioPrivate' /> <b>Private (recommended)</b></p>"+
						"<p><input type='radio' name='publicSettings' value='r' id='publicSettingRadioReadOnly' /> Public read only</p>"+
						"<p><input type='radio' name='publicSettings' value='rw' id='publicSettingRadioEditable' /> Publicly editable (not recommended)</p>"+
				"</form>"
				));
			
			//Set selected based on settings
			if(users.isPublic()) {
				if(users.isPublicReadOnly()) {
					$("#publicSettingRadioReadOnly").attr("checked", true);
				} else {
					$("#publicSettingRadioEditable").attr("checked", true);
				}
			} else {
				$("#publicSettingRadioPrivate").attr("checked", true);
			}
			
			//Add buttons
			actions.append(elementFactory("button", {"class":"waveButton ui-state-default ui-corner-all"}, "update", actionFactory.submitPublic));
			actions.append(elementFactory("button", {"class":"waveButton ui-state-default ui-corner-all"}, "back", actionFactory.back));
					
			
	        gadgets.window.adjustHeight();
		},
		addEmail		: 	function(state) {
			state = state || wave.getState();
			var gadgetContent = $('#content');
			var actions = $('#actions');
			gadgetContent.children().remove();
			actions.children().remove();
			var users = new Users(state);
			
			gadgetContent.append($(
				"<dl>" +
					"<dt>E-mail address:</dt>"+
					"<dd><input type='text' class='textInput ui-state-default ui-corner-all' id='newEmailInput'></input></dd>"+
					"<dt></dt>"+
					"<dd><div id='emailError' class='attention ui-state-error ui-corner-all' style='visibility:hidden;'></div></dd>"+
					"<dt>Personal message:</dt>"+
					"<dd><textarea id='messageInput' rows='2' cols='20' class='ui-state-default ui-corner-all'></textarea></dd>"+
				"</dl>"
				));
				
			//Add buttons
			actions.append(elementFactory("button", {"class":"waveButton ui-state-default ui-corner-all"}, "add", actionFactory.submitNewEmail));
			actions.append(elementFactory("button", {"class":"waveButton ui-state-default ui-corner-all"}, "back", actionFactory.back));
			
	        gadgets.window.adjustHeight();
		},
		working			: 	function() {
		    isActioning = false;
			var gadgetContent = $('#content');
			var actions = $('#actions');
			gadgetContent.children().remove();
			actions.children().remove();
			gadgetContent.append(elementFactory("img",
				{
					"src"	: "http://mr-ray.appspot.com/web/media/workingbar.gif"
				},
				false,
				false));
			gadgets.window.adjustHeight();
		}, 
	};
	
	/*************************************************************************
	* Objects
	*************************************************************************/
	
	/**
	* Models a command to be sent to the robot
	* @param action: the action to send
	* @param params: the parameters to send
	*/
	var Command = function(action, params) {
		var self = this;
		self.action = action;
		self.params = params;
		self.rawJson = null;
		
		/**
		* Builds the outgoing json
		* @return the Command object (allows for chaining)
		*/
		self.build = function() {
			self.rawJson = JSON.stringify({action : action, params : params});
			return self;
		};
		
		/**
		* @return the json object to be sent to the robot or null
		*/
		self.getJson = function() {
			return self.rawJson || null;
		};
		
		/**
		* Sends the command to the robot
		* @param state: the wave state or null if it is not available
		*/
		self.send = function(state) {
			state = state || wave.getState();
			state.submitValue("command_"+utils.getViewer(), Base64.encode(self.rawJson));
		};
	};
	
	/**
	* Models the set of participants in this wave
	*/
	var WaveParticipants = function() {
		var self = this;
		self.requestStates = {
			fetch	: "fetch",
			updated	: "updated",
			idle	: null 
		};
		self.participants = null;
		
		/**
		* Builds the list of participants
		* @return the WaveParticipants object (allows for chaining)
		*/
		self.build = function() {
			var rawParticipants = wave.getParticipants();
			participants = {};
			for(var i=0; i < rawParticipants.length; i++) {
				var rawParticipant = rawParticipants[i];
				participants[rawParticipant.getId()] =
							{displayName 	: rawParticipant.getDisplayName(),
							thumbUrl		: rawParticipant.getThumbnailUrl()};
			}
			self.participants = JSON.stringify(participants);
			return self;
		};
		
		/**
		* Submits the list of participants to the robot
		* @param state: the wave state or null if it is not available
		*/
		self.send = function(state) {
			state = state || wave.getState();
			state.submitValue("participantDetails", Base64.encode(self.participants));
		};
		
		/**
		* Updates the state only when requested by the robot
		* @param state: the wave state or null if it is not available
		*/
		self.update = function(state) {
			state = state || wave.getState();
			if (state.get("participantDetailsState") === self.requestStates['fetch']) {
				self.build().send(state);
				state.submitValue("participantDetailsState", self.requestStates['updated']);
			}
		};
	}
	
	/**
	* Represents participants including public settings in a javascript way
	* @param state: the current state from wave
	*/
	var Users = function(state) {
		var self = this;
		self.state = state;
		self.rawData = state.get("state");
		if (self.rawData !== null) {
			self.rawJson = JSON.parse(Base64.decode(self.rawData));
		} else {
			self.rawJson = "";
		}
		
		/**
		* @return list of email participants, [] if none specified
		*/
		self.getEmailUsers = function() {
			return self.rawJson['emailParticipants'] || [].sort();
		};
		
		/**
		* @return the public map or an empty map if not found
		*/
		self.getPublic = function() {
		    return self.rawJson['public'] || {}
		}
		
		/**
		* @return public status, false if none specified
		*/
		self.isPublic = function() {
		    var isPublic = self.getPublic()['isPublic'];
		    if(isPublic === undefined) {
		        return false;
		    } else {
		        return isPublic;
		    }
		};
		
		/**
		* @return read only status, false if none specified
		*/
		self.isPublicReadOnly = function() {
		    var isReadOnly =  self.getPublic()['isReadOnly'];
		    if(isReadOnly === undefined) {
		        return true;
		    } else {
		        return isReadOnly;
		    }
		};
		
		/**
		* @return public url, "" if none specified
		*/
		self.getPublicUrl = function() {
			return self.rawJson['public']['url'] || "";
		};
		
		/**
		* @param email: an email address to validate
		* @return true if it is valid
		*/
		self.isEmailValid = function(email) {
			var emailPattern = /^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,4}$/;
	        return emailPattern.test(email);
		}
		
		/**
		* @param email: an address to check against the current list of addres'
		* @return true if the address is already present in the list of email
		* participants
		*/
		self.isUserAlreadyAdded = function(email) {
			var emailList = self.getEmailUsers();
			for(var i = 0; i < emailList.length; i++) {
				if(email === emailList[i]) {
					return true;
				}
			}
			return false;
		}
		
		/**
		* Adds an email user for submission to the wave server and submits
		* @param email: the email address to add
		* @param message: a message for the recipient
		* @return true if the user could be added. false indicates an error
		*/
		self.addEmailUser = function(email, message) {
			if(self.isEmailValid(email) && !self.isUserAlreadyAdded(email)) {
				new Command(actions['addEmail'],
							{email:email, message:message}).build().send(self.state);
				return true;
			}
			return false;
		};
		
		/**
		* Removes an email user and submits to the wave servers
		* @param email: the email address to remove
		* @return true if the user could be deleted. false indicates an error
		*/
		self.removeEmailUser = function(email) {
			if(self.isEmailValid(email) && self.isUserAlreadyAdded(email)) {
				new Command(actions['deleteEmail'],
							{email : email}).build().send(self.state);
				return true;
			}
			return false;
		};
		
		/**
		* Changes the public settings of this wave and submits
		* @param isPublic: true or false
		* @param isReadOnly: true or false
		*/
		self.changePublic = function(isPublic, isReadOnly) {
			new Command(actions['changePublic'],
							{isPublic : isPublic,
							isReadOnly: isReadOnly }).build().send(self.state);
		};
	};
	
	/*************************************************************************
	* Wave / document functions
	*************************************************************************/
	
    /**
    * Redraws the gadget
    */
    var update = function() {
		var state = wave.getState();
		//Empty out the command variable
		sentCommand = state.get("command_" + utils.getViewer());
		
		//Run tasks on first load
		if (!documentInitialized) {
			renderFactory.list(state);
			documentInitialized = true;
		}
		
		//Update the participant profiles
		//new WaveParticipants().update();
		
		//Update the screen
		if (canReloadPage()) {
			renderFactory.list(state);
		}
    };
    
	/**
	* Google API initializing--registering handler etc
	*/
	function init() {
		if (wave && wave.isInWaveContainer()) {
			wave.setStateCallback(update);
		}
	}
	gadgets.util.registerOnLoadHandler(init);
    

    /**
    * Run when document is initialized
    */
    $(document).ready(function() {
        
    });
	
})(jQuery);