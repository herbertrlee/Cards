package com.herb.cards.main;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

import android.graphics.drawable.Drawable;
import android.os.Bundle;
import android.support.v4.app.Fragment;
import android.util.Log;
import android.util.TypedValue;
import android.view.GestureDetector;
import android.view.Gravity;
import android.view.LayoutInflater;
import android.view.MotionEvent;
import android.view.View;
import android.view.View.OnClickListener;
import android.view.ViewGroup.LayoutParams;
import android.view.animation.TranslateAnimation;
import android.view.ViewGroup;
import android.widget.AdapterView;
import android.widget.AdapterView.OnItemSelectedListener;
import android.widget.ArrayAdapter;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import android.widget.RadioButton;
import android.widget.RadioGroup;
import android.widget.RadioGroup.OnCheckedChangeListener;
import android.widget.Spinner;
import android.widget.TextView;

public class GameHistoryFragment extends Fragment implements OnClickListener, OnCheckedChangeListener, OnItemSelectedListener
{
	public interface Listener
	{
		public abstract void pageForward();
		public abstract void pageBackward();
		public abstract void jumpToPage(int i);
	}
	
	private Listener listener;
	
	private static int[] CLICKABLES = {R.id.forward_button, R.id.back_button};
	
	private String gameName = "", gameId = "", czarName = "", winnerName = "";
	private String blackCardText = "";
	private int roundNumber = 0, pick = 0, currentRound = 0;
	private String[] playerNames = {};
	private JSONArray[] whiteCardTexts = {};
	
	TextView headerTextView, blackCardTextView;
	LinearLayout[] submissionLayouts;
	FrameLayout submissionLayout;
	RadioGroup playerNameRadioGroup;
	Spinner roundSpinner;
	private int topSubmission = -1, bottomSubmission = -1;
	
	GestureDetector gesture;
	
	@Override
	public View onCreateView(LayoutInflater inflater, ViewGroup container, Bundle savedInstanceState)
	{
		View v = inflater.inflate(R.layout.fragment_game_history_screen, container, false);
		
		for(int i : CLICKABLES)
			v.findViewById(i).setOnClickListener(this);
			
		headerTextView = (TextView) v.findViewById(R.id.game_history_header_text_view);
		blackCardTextView = (TextView) v.findViewById(R.id.black_card_history_text_view);
		submissionLayout = (FrameLayout) v.findViewById(R.id.submission_history_container);
		playerNameRadioGroup = (RadioGroup) v.findViewById(R.id.player_radio_group);
		roundSpinner = (Spinner) v.findViewById(R.id.round_select_spinner);
		
		playerNameRadioGroup.setOnCheckedChangeListener(this);
		roundSpinner.setOnItemSelectedListener(this);
		
		gesture = new GestureDetector(getActivity(), new HistoryGestureListener());
		
		return v;
	}

	@Override
	public void onClick(View v)
	{
		switch(v.getId())
		{
			case R.id.forward_button:
				listener.pageForward();
				break;
			case R.id.back_button:
				listener.pageBackward();
				break;
			default:
				break;
		}
	}

	public void setListener(Listener listener)
	{
		this.listener = listener;
	}
	
	public void setCurrentRound(int round)
	{
		currentRound = round;
	}
	
	public void setRoundInfo(JSONObject roundInfoJSON) throws JSONException
	{
		czarName = roundInfoJSON.getString("czarName");
		winnerName = roundInfoJSON.getString("winnerName");
		roundNumber = roundInfoJSON.getInt("roundNumber");
	}
	
	public void setSubmissionInfo(JSONArray submissionJSON) throws JSONException
	{
		int length = submissionJSON.length();
		playerNames = new String[length];
		whiteCardTexts = new JSONArray[length];
		
		for(int i=0;i<length;i++)
		{
			JSONObject submission = submissionJSON.getJSONObject(i);
			playerNames[i] = submission.getString("userAlias");
			
			whiteCardTexts[i] = new JSONArray();
			JSONArray whiteCardInfos = submission.getJSONArray("whiteCardInfos");
			for(int j=0;j<whiteCardInfos.length();j++)
			{
				JSONObject whiteCardInfo = whiteCardInfos.getJSONObject(j);
				whiteCardTexts[i].put(whiteCardInfo.getString("text"));
			}
		}
		
		bottomSubmission = 0;
		topSubmission = length - 1;
	}
	
	public void setBlackCard(JSONObject blackCardJSON)
	{
		try
		{
			pick = blackCardJSON.getInt("pick");
			blackCardText = blackCardJSON.getString("text");
		} catch (JSONException e)
		{
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
	}
	
	public void updateUi()
	{
		if(getActivity() == null)
			return;
		
		if(listener == null)
			return;
		
		headerTextView.setText(String.format("Round %d - %s picked", roundNumber, czarName));
		blackCardTextView.setText(blackCardText);
		
		submissionLayout.removeAllViews();
		submissionLayouts = new LinearLayout[whiteCardTexts.length];
		
		playerNameRadioGroup.removeAllViews();
		
		int pixelWidth = (int) TypedValue.applyDimension(TypedValue.COMPLEX_UNIT_SP, 150, getResources().getDisplayMetrics());
		int pixelHeight = (int) TypedValue.applyDimension(TypedValue.COMPLEX_UNIT_SP, 200, getResources().getDisplayMetrics());
		int dp10 = (int) TypedValue.applyDimension(TypedValue.COMPLEX_UNIT_SP, 10, getResources().getDisplayMetrics());
		
		if(pick == 3)
		{
			pixelWidth = (int) TypedValue.applyDimension(TypedValue.COMPLEX_UNIT_SP, 100, getResources().getDisplayMetrics());
		}
		
		Drawable star = getResources().getDrawable(R.drawable.ic_action_important);
		
		for(int i=0;i<whiteCardTexts.length;i++)
		{
			RadioButton playerRadioButton = new RadioButton(getActivity());
			playerRadioButton.setText(playerNames[i]);
			playerRadioButton.setId(i);
			
			if(i == whiteCardTexts.length - 1)
				playerRadioButton.setChecked(true);
			
			if(playerNames[i].equals(winnerName))
				playerRadioButton.setCompoundDrawablesWithIntrinsicBounds(star, null, star, null);
			
			playerNameRadioGroup.addView(playerRadioButton);
			
			LinearLayout submissionPage = new LinearLayout(getActivity());
			submissionPage.setOrientation(LinearLayout.HORIZONTAL);
			submissionPage.setGravity(Gravity.CENTER);
			FrameLayout.LayoutParams flp = new FrameLayout.LayoutParams(LayoutParams.MATCH_PARENT, pixelHeight);
			flp.setMargins(0, dp10, 0, 0);
			submissionPage.setLayoutParams(flp);
			
			for(int j=0;j<pick;j++)
			{
				TextView whiteCardTextView = new TextView(getActivity());
				try
				{
					whiteCardTextView.setText(whiteCardTexts[i].getString(j));
				} catch (JSONException e)
				{
					// TODO Auto-generated catch block
					e.printStackTrace();
				}
				LinearLayout.LayoutParams llp = new LinearLayout.LayoutParams(pixelWidth, pixelHeight);
				if(j!=pick)
					llp.setMargins(0, 0, dp10, 0);
				whiteCardTextView.setLayoutParams(llp);
				whiteCardTextView.setBackground(getResources().getDrawable(R.drawable.white_card));
				whiteCardTextView.setTextAppearance(getActivity(), R.style.WhiteCard);
				
				if(playerNames[i].equals(winnerName))
				{
					whiteCardTextView.setCompoundDrawablesWithIntrinsicBounds(null, null, null, star);
				}
				
				whiteCardTextView.setOnTouchListener(new View.OnTouchListener()
				{
					
					@Override
					public boolean onTouch(View v, MotionEvent event)
					{
						return gesture.onTouchEvent(event);
					}
				});
				
				submissionPage.addView(whiteCardTextView);
			}
			
			submissionLayouts[i] = submissionPage;
			submissionLayout.addView(submissionPage);
		}
		
		String[] rounds = new String[currentRound];
		
		for(int i=0;i<rounds.length;i++)
		{
			if(i==0)
				rounds[i] = "Round:";
			else
				rounds[i] = Integer.toString(i);
		}
		
		ArrayAdapter<String> adapter = new ArrayAdapter<String>(getActivity(), android.R.layout.simple_spinner_item, rounds);
		
		roundSpinner.setAdapter(adapter);
		roundSpinner.setSelection(0);
	}
		
	class HistoryGestureListener extends GestureDetector.SimpleOnGestureListener
	{
		@Override
		public boolean onDown(MotionEvent e)
		{
			return true;
		}
		
		@Override
		public boolean onFling(MotionEvent e1, MotionEvent e2, float velocityX, float velocityY)
		{
			if(e1.getX() > e2.getX())
				scrollSubmissionsForward();
			else
				scrollSubmissionsBackward();
			
			return true;
		}
	}

	public void scrollSubmissionsBackward()
	{
		LinearLayout topLayout = submissionLayouts[topSubmission];
		
		float pixelWidth = topLayout.getWidth();
		
		topSubmission++;
		bottomSubmission++;
		
		if(topSubmission == submissionLayouts.length)
			topSubmission = 0;
		if(bottomSubmission == submissionLayouts.length)
			bottomSubmission = 0;

		submissionLayouts[topSubmission].bringToFront();
		playerNameRadioGroup.check(topSubmission);
		
		TranslateAnimation anim = new TranslateAnimation(pixelWidth, 0f, 0f, 0f);
		anim.setDuration(500);
		topLayout.startAnimation(anim);
	}

	public void scrollSubmissionsForward()
	{
		LinearLayout topLayout = submissionLayouts[topSubmission];

		float pixelWidth = topLayout.getWidth();
		
		topSubmission--;
		bottomSubmission--;
		
		if(topSubmission == -1)
			topSubmission = submissionLayouts.length - 1;
		if(bottomSubmission == -1)
			bottomSubmission = submissionLayouts.length - 1;
		
		submissionLayouts[topSubmission].bringToFront();
		playerNameRadioGroup.check(topSubmission);
		
		TranslateAnimation anim = new TranslateAnimation(-pixelWidth, 0f, 0f, 0f);
		anim.setDuration(500);
		topLayout.startAnimation(anim);
	}
	
	public void scroll()
	{
		LinearLayout topLayout = submissionLayouts[topSubmission];

		float pixelWidth = topLayout.getWidth();
		
		topSubmission--;
		bottomSubmission--;
		
		if(topSubmission == -1)
			topSubmission = submissionLayouts.length - 1;
		if(bottomSubmission == -1)
			bottomSubmission = submissionLayouts.length - 1;
		
		submissionLayouts[topSubmission].bringToFront();
		
		TranslateAnimation anim = new TranslateAnimation(-pixelWidth, 0f, 0f, 0f);
		anim.setDuration(500);
		topLayout.startAnimation(anim);
	}

	@Override
	public void onCheckedChanged(RadioGroup group, int checkedId)
	{
		while(checkedId != topSubmission)
			scroll();
	}

	@Override
	public void onItemSelected(AdapterView<?> parent, View view, int position,
			long id)
	{
		if(position != 0)
			listener.jumpToPage(currentRound - position - 1);
	}

	@Override
	public void onNothingSelected(AdapterView<?> parent)
	{
	}

}
